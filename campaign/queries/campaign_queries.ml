(* State queries of the case-study campaign.

   Loaded into Frama-C after an Eva analysis, or after [-load] of a session
   saved by one, this module writes the answers of enumerated and named state
   queries to the file named by the environment variable
   [CAMPAIGN_QUERIES_OUT]. Without that variable it writes no answer.

   A query is a statement, a point (before or after the statement), a
   callstack or all callstacks (written [*]), and a scalar lvalue. The
   enumerated queries are, for every reached statement of every function with
   a body, the scalar lvalues that occur in the statement itself: its
   instruction, or the expression of a condition, a switch or a return. The
   named queries are read from the file named by [CAMPAIGN_QUERIES_NAMED], one
   per line: FUNCTION LINE POINT VARIABLE, separated by tabulations. They ask
   for a variable before or after each statement of FUNCTION at LINE.

   Statements and callstacks are written with keys that do not depend on the
   internal numbering of the AST: a statement is FUNCTION:LINE:K where K is
   the rank of the statement among those of FUNCTION at LINE, in the order of
   [sallstmts]; a callstack is the entry point followed by CALLEE@CALLSITE for
   each call, from the outermost.

   The exit queries ask, for every function whose return statement is
   reached, for each scalar lvalue that occurs in its body, in the state at
   the end of the function ([Eva.Results.at_end_of]): its exit state. Their
   statement is written FUNCTION:exit and their point [exit].

   A query is answered only when the state of its function was saved. The
   results of a function are not saved with [-eva-no-results], or for a
   function analysed through its specification or a builtin
   ([Eva.Results.are_available]); the states of the cvalue domain are not
   saved with [-eva-no-results-domain cvalue], and Eva then gives the top
   state of that domain at every point. In both cases the
   query is written as unavailable, never evaluated, whether it is a query of
   a statement or of the exit.

   Output, tab-separated:
   - [format 2] first: the exit points are declared reached;
   - [reach FUNCTION STMT] for each reached statement, and [reach FUNCTION
     FUNCTION:exit] for each function whose return statement is reached;
   - [answer FUNCTION STMT POINT CALLSTACK LVALUE INIT ESC VALUE] where INIT
     and ESC tell whether the value may be uninitialized or an escaping
     address, and VALUE is written as described at [value_to_string];
   - [unavailable FUNCTION STMT POINT CALLSTACK LVALUE REASON] when the state
     of the query was not saved: [no-results] when the results of the
     function are not available, [disabled-domain] when the states of the
     cvalue domain were not saved or the domain is disabled, [top-state]
     when Eva returns no state for the query; the queries of a function
     whose state was not saved are written over all callstacks only;
   - [error FUNCTION STMT POINT CALLSTACK LVALUE REASON] when the evaluation
     raises an exception;
   - [done COUNT] at the end, with the number of answer, unavailable and
     error lines written before it. A file without this line, or whose count
     differs, is incomplete.

   With the environment variable [CAMPAIGN_AST_OUT], the module also writes
   to the file it names the identity of the AST, whether Eva ran or not (a
   session saved after parsing is enough): one line per statement of each
   function with a body, in the order of the globals and of [sallstmts],

     stmt FUNCTION SID LOCATION TEXT

   where SID is the number of the statement, LOCATION its source location as
   Frama-C prints it (relative to the current directory), and TEXT the
   statement itself, without the statements it contains, which are named by
   their numbers. The file ends with [done COUNT], the number of statement
   lines. Two runs number the statements of their programs alike when these
   lines are the same. *)

open Cil_types

(* ----- Keys --------------------------------------------------------------- *)

let stmt_keys : (int, string) Hashtbl.t = Hashtbl.create 997

let compute_stmt_keys kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    let name = Kernel_function.get_name kf in
    let ranks = Hashtbl.create 17 in
    List.iter
      (fun stmt ->
         let line = Fileloc.line (Cil_datatype.Stmt.loc stmt) in
         let rank = Option.value ~default:0 (Hashtbl.find_opt ranks line) in
         Hashtbl.replace ranks line (rank + 1);
         Hashtbl.replace stmt_keys stmt.sid
           (Printf.sprintf "%s:%d:%d" name line rank))
      fundec.sallstmts

let stmt_key stmt =
  match Hashtbl.find_opt stmt_keys stmt.sid with
  | Some key -> key
  | None -> Printf.sprintf "?:%d" stmt.sid

let callstack_key (cs : Eva.Callstack.t) =
  let calls =
    List.rev_map
      (fun (kf, stmt) ->
         Printf.sprintf "%s@%s" (Kernel_function.get_name kf) (stmt_key stmt))
      cs.stack
  in
  String.concat "|" (Kernel_function.get_name cs.entry_point :: calls)

(* ----- Values ------------------------------------------------------------- *)

let bound = function
  | None -> ""
  | Some z -> Z.to_string z

(* Integers: [S] followed by the elements of a small set, separated by
   commas; or [I] followed by MIN..MAX%REM/MODULO, an empty bound being
   unbounded. Floats: [F] followed by MIN..MAX in hexadecimal notation, then
   [;nan] when NaN is possible; [Fnan] for NaN alone. *)
let ival_to_string ival =
  if Ival.is_bottom ival then "B"
  else if Ival.is_int ival then
    match Ival.project_small_set ival with
    | Some l -> "S" ^ String.concat "," (List.map Z.to_string l)
    | None ->
      let min, max, rem, modu = Ival.min_max_r_mod ival in
      Printf.sprintf "I%s..%s%%%s/%s"
        (bound min) (bound max) (Z.to_string rem) (Z.to_string modu)
  else
    match Ival.min_and_max_float ival with
    | None, _ -> "Fnan"
    | Some (min, max), nan ->
      Printf.sprintf "F%h..%h%s"
        (Fval.F.to_float min) (Fval.F.to_float max)
        (if nan then ";nan" else "")

(* A name for a base that does not depend on the numbering of variables:
   the name of a global, NAME@FUNCTION for a local or a formal, and the
   printed form of other bases. *)
let base_name base =
  if Base.is_null base then "NULL"
  else
    match base with
    | Base.Var (vi, _) | Base.Allocated (vi, _, _) ->
      if vi.vglob then vi.vname
      else begin
        match Kernel_function.find_defining_kf vi with
        | Some kf -> vi.vname ^ "@" ^ Kernel_function.get_name kf
        | None -> vi.vname
      end
    | _ -> Format.asprintf "%a" Base.pretty base

let escape s =
  String.map (function '\t' | '\n' | ';' | '=' -> '_' | c -> c) s

(* [T] for the top value; [G] followed by the names of the bases of a
   garbled mix; otherwise [M] followed by BASE=OFFSETS for each base, sorted
   by name, separated by semicolons. The base NULL holds the integers. *)
let value_to_string (v : Cvalue.V.t) =
  match v with
  | Top (Base.SetLattice.Top, _) -> "T"
  | Top (Base.SetLattice.Set bases, _) ->
    let names = Base.Hptset.fold (fun b acc -> base_name b :: acc) bases [] in
    "G" ^ String.concat ";" (List.sort String.compare (List.map escape names))
  | Map m ->
    let entries =
      Cvalue.V.M.fold
        (fun b ival acc ->
           (escape (base_name b) ^ "=" ^ ival_to_string ival) :: acc)
        m []
    in
    "M" ^ String.concat ";" (List.sort String.compare entries)

(* ----- Queries ------------------------------------------------------------ *)

let is_scalar typ =
  Ast_types.C.is_scalar typ

(* The scalar lvalues of the statement itself, without those of the blocks
   it contains. *)
let lvals_of_stmt stmt =
  let found = ref [] in
  let visitor = object
    inherit Visitor.frama_c_inplace
    method! vlval lv =
      if is_scalar (Cil.typeOfLval lv) then found := lv :: !found;
      Cil.DoChildren
  end in
  let visit_exp e = ignore (Visitor.visitFramacExpr visitor e) in
  begin match stmt.skind with
    | Instr instr -> ignore (Visitor.visitFramacInstr visitor instr)
    | Return (Some e, _) | If (e, _, _, _) | Switch (e, _, _, _) ->
      visit_exp e
    | _ -> ()
  end;
  let module S = Cil_datatype.LvalStructEq.Set in
  S.elements (S.of_list !found)

let out = ref stdout
let count = ref 0

let print fmt = Printf.fprintf !out fmt

let point_name = function
  | `Before -> "before"
  | `After -> "after"
  | `Exit -> "exit"

let unavailable fname skey point cs_key lval_text reason =
  incr count;
  print "unavailable\t%s\t%s\t%s\t%s\t%s\t%s\n"
    fname skey (point_name point) cs_key lval_text reason

(* Whether Eva saved the states of the cvalue domain. It does not when the
   option -eva-no-results-domain names that domain; the option is saved with
   the session. Its value is the text of its settings in their order: a
   comma-separated list where NAME or +NAME adds a domain, -NAME removes it,
   and @default stands for the default value, which is empty. *)
let cvalue_states_saved =
  lazy
    (match Typed_parameter.get "-eva-no-results-domain" with
     | exception Not_found -> true
     | parameter ->
       List.fold_left
         (fun saved item ->
            match item with
            | "cvalue" | "+cvalue" -> false
            | "-cvalue" -> true
            | _ -> saved)
         true
         (String.split_on_char ',' (Typed_parameter.get_value parameter)))

(* Whether the state of a function was saved, checked once per function
   before any evaluation: the evaluation in a state that was not saved gives
   a top value. [Unavailable "no-results"] when the results of the function
   are not available, [Unavailable "disabled-domain"] when the states of the
   cvalue domain were not saved: Eva then gives the top state of that domain
   at every point. *)
type availability = Available | Unavailable of string

let availability kf =
  if not (Eva.Results.are_available kf) then Unavailable "no-results"
  else if not (Lazy.force cvalue_states_saved) then
    Unavailable "disabled-domain"
  else Available

(* Writes the answer of one query, or the reason why the state of its
   function is not available. *)
let answer ~availability ~fname ~skey point cs_key request lval_text eval =
  let point_text = point_name point in
  match availability with
  | Unavailable reason ->
    unavailable fname skey point cs_key lval_text reason
  | Available ->
    match eval request with
    | exception exn ->
      incr count;
      print "error\t%s\t%s\t%s\t%s\t%s\t%s\n"
        fname skey point_text cs_key lval_text
        (escape (Printexc.to_string exn))
    | eval ->
      match Eva.Results.as_cvalue_result eval with
      | Error Eva.Results.Top ->
        unavailable fname skey point cs_key lval_text "top-state"
      | Error Eva.Results.DisabledDomain ->
        unavailable fname skey point cs_key lval_text "disabled-domain"
      | Ok _ | Error Eva.Results.Bottom ->
        incr count;
        let v = Eva.Results.as_cvalue_or_uninitialized eval in
        let init =
          if Cvalue.V_Or_Uninitialized.is_initialized v then 1 else 0
        in
        let esc = if Cvalue.V_Or_Uninitialized.is_noesc v then 0 else 1 in
        let value = Cvalue.V_Or_Uninitialized.get_v v in
        let value =
          if Cvalue.V.is_bottom value && Eva.Results.is_empty request
          then "B" else value_to_string value
        in
        print "answer\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%s\n"
          fname skey point_text cs_key lval_text init esc value

(* The requests of a query: over all callstacks ([*]), then in each
   callstack in which the point is reached. *)
let requests_at before after =
  let callstacks =
    Eva.Results.callstacks before @ Eva.Results.callstacks after
    |> List.sort_uniq Eva.Callstack.compare
  in
  ("*", before, after)
  :: List.map
    (fun cs ->
       callstack_key cs,
       Eva.Results.in_callstack cs before, Eva.Results.in_callstack cs after)
    callstacks

(* The requests of a statement: in each callstack when the state of its
   function was saved, over all callstacks only otherwise. *)
let requests availability stmt =
  let before = Eva.Results.before stmt and after = Eva.Results.after stmt in
  match availability with
  | Available -> requests_at before after
  | Unavailable _ -> [ "*", before, after ]

let query_stmt ~availability kf stmt lvals =
  let fname = Kernel_function.get_name kf and skey = stmt_key stmt in
  List.iter
    (fun (cs_key, before, after) ->
       List.iter
         (fun (text, eval) ->
            answer ~availability ~fname ~skey `Before cs_key before text eval;
            answer ~availability ~fname ~skey `After cs_key after text eval)
         lvals)
    (requests availability stmt)

let lval_query lv =
  Format.asprintf "%a" Printer.pp_lval lv, Eva.Results.eval_lval lv

let enumerated kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    let availability = availability kf in
    List.iter
      (fun stmt ->
         if Eva.Results.is_reachable stmt then begin
           print "reach\t%s\t%s\n" (Kernel_function.get_name kf)
             (stmt_key stmt);
           query_stmt ~availability kf stmt
             (List.map lval_query (lvals_of_stmt stmt))
         end)
      fundec.sallstmts

(* The exit queries of a function: the scalar lvalues of its body, in the
   state at the end of the function, when its return statement is reached.
   They go through the same check of availability as the queries of the
   statements: a function whose state was not saved gets one unavailable
   line per lvalue, over all callstacks. *)
let exit_queries kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    match Kernel_function.find_return kf with
    | exception Kernel_function.No_Statement -> ()
    | return ->
      if Eva.Results.is_reachable return then begin
        let module S = Cil_datatype.LvalStructEq.Set in
        let lvals =
          List.fold_left (fun acc stmt -> S.union acc (S.of_list
                                                        (lvals_of_stmt stmt)))
            S.empty fundec.sallstmts
        in
        let fname = Kernel_function.get_name kf in
        let skey = fname ^ ":exit" in
        print "reach\t%s\t%s\n" fname skey;
        let availability = availability kf in
        let at_end = Eva.Results.at_end_of kf in
        let requests =
          match availability with
          | Available -> requests_at at_end at_end
          | Unavailable _ -> [ "*", at_end, at_end ]
        in
        List.iter
          (fun (cs_key, _, request) ->
             S.iter
               (fun lv ->
                  let text, eval = lval_query lv in
                  answer ~availability ~fname ~skey `Exit cs_key request text
                    eval)
               lvals)
          requests
      end

let find_variable kf name =
  let locals = Kernel_function.(get_formals kf @ get_locals kf) in
  match List.find_opt (fun vi -> vi.vname = name) locals with
  | Some vi -> Some vi
  | None ->
    try Some (Globals.Vars.find_from_astinfo name Global)
    with Not_found -> None

let named file =
  let channel = open_in file in
  let rec loop () =
    match input_line channel with
    | exception End_of_file -> close_in channel
    | line ->
      begin match String.split_on_char '\t' line with
        | [ fname; line_no; point; var ] ->
          let kf = Globals.Functions.find_by_name fname in
          let line_no = int_of_string line_no in
          let vi =
            match find_variable kf var with
            | Some vi -> vi
            | None -> failwith ("unknown variable " ^ var)
          in
          let text = "named:" ^ var and eval = Eva.Results.eval_var vi in
          let availability = availability kf in
          let fname = Kernel_function.get_name kf in
          let stmts = (Kernel_function.get_definition kf).sallstmts in
          List.iter
            (fun stmt ->
               let loc = Cil_datatype.Stmt.loc stmt in
               let skey = stmt_key stmt in
               if Fileloc.line loc = line_no then
                 List.iter
                   (fun (cs_key, before, after) ->
                      match point with
                      | "before" ->
                        answer ~availability ~fname ~skey `Before cs_key
                          before text eval
                      | "after" ->
                        answer ~availability ~fname ~skey `After cs_key
                          after text eval
                      | _ -> failwith ("unknown point " ^ point))
                   (requests availability stmt))
            stmts
        | [] | [ "" ] -> ()
        | _ -> failwith ("malformed named query: " ^ line)
      end;
      loop ()
  in
  loop ()

(* ----- Identity of the AST ---------------------------------------------- *)

let flat text =
  String.map (function '\t' | '\n' | '\r' -> ' ' | c -> c) text

let sids stmts =
  String.concat "," (List.map (fun s -> string_of_int s.sid) stmts)

(* The statement itself, its labels included, without the statements it
   contains: those are named by their numbers. *)
let stmt_text stmt =
  let p = Format.asprintf in
  let body =
    match stmt.skind with
    | Instr instr -> p "%a" Printer.pp_instr instr
    | Return (None, _) -> "return"
    | Return (Some e, _) -> p "return %a" Printer.pp_exp e
    | Goto (target, _) -> p "goto %d" !target.sid
    | Break _ -> "break"
    | Continue _ -> "continue"
    | If (e, b1, b2, _) ->
      p "if %a then {%s} else {%s}" Printer.pp_exp e (sids b1.bstmts)
        (sids b2.bstmts)
    | Switch (e, b, cases, _) ->
      p "switch %a {%s} cases {%s}" Printer.pp_exp e (sids b.bstmts)
        (sids cases)
    | Loop (_, b, _, _, _) -> p "loop {%s}" (sids b.bstmts)
    | Block b -> p "block {%s}" (sids b.bstmts)
    | UnspecifiedSequence l ->
      p "sequence {%s}" (sids (List.map (fun (s, _, _, _, _) -> s) l))
    | Throw _ | TryCatch _ | TryFinally _ | TryExcept _ ->
      p "%a" Printer.pp_stmt stmt
  in
  let labels = List.map (fun l -> p "%a" Printer.pp_label l) stmt.labels in
  flat (String.concat " " (labels @ [ body ]))

(* The source range of a statement or a global: the file and line where it
   starts, as Frama-C prints them (relative to the current directory), then
   the line and column of its start and of its end in the text that was
   parsed, after preprocessing. Two occurrences of one text on one line, such
   as the two branches of [if (c) f(1); else f(1);], have different
   columns. *)
let range = function
  | None -> "-"
  | Some loc ->
    let start, stop = Fileloc.positions loc in
    if Filepos.is_empty start then "-"
    else
      let original = Filepos.original start in
      Printf.sprintf "%s:%d@%d:%d-%d:%d"
        (Filepath.to_string (Filepos.path original)) (Filepos.line original)
        (Filepos.input_line start) (Filepos.input_column start)
        (Filepos.input_line stop) (Filepos.input_column stop)

(* A global without the body or the contract of a function: the body is
   listed statement by statement, and the analysis may add a contract to a
   function that has none. *)
let global_line g =
  let p = Format.asprintf in
  match g with
  | GFun (fundec, loc) ->
    let locals = List.map (p "%a" Printer.pp_vdecl) fundec.slocals in
    "function", fundec.svar.vname, Some loc,
    p "%a; locals {%s}" Printer.pp_vdecl fundec.svar
      (String.concat "; " locals)
  | GFunDecl (_, vi, loc) ->
    "declaration", vi.vname, Some loc, p "%a" Printer.pp_vdecl vi
  | GVarDecl (vi, loc) ->
    "variable", vi.vname, Some loc, p "%a" Printer.pp_global g
  | GVar (vi, _, loc) ->
    "definition", vi.vname, Some loc, p "%a" Printer.pp_global g
  | GType (ti, loc) -> "type", ti.tname, Some loc, p "%a" Printer.pp_global g
  | GCompTag (ci, loc) | GCompTagDecl (ci, loc) ->
    "composite", ci.cname, Some loc, p "%a" Printer.pp_global g
  | GEnumTag (ei, loc) | GEnumTagDecl (ei, loc) ->
    "enumeration", ei.ename, Some loc, p "%a" Printer.pp_global g
  | GAnnot (_, loc) -> "annotation", "-", Some loc, p "%a" Printer.pp_global g
  | GAsm (_, loc) -> "asm", "-", Some loc, p "%a" Printer.pp_global g
  | GPragma (_, loc) -> "pragma", "-", Some loc, p "%a" Printer.pp_global g
  | GText text -> "text", "-", None, text

(* The AST listing: the line "format 2", then for each global a line
   [global KIND NAME RANGE TEXT], followed for a function by a line
   [stmt FUNCTION SID RANGE TEXT] for each of its statements, then the line
   [done COUNT], COUNT being the number of global and stmt lines. The
   format 1, written by earlier revisions, listed the statements alone,
   without their columns. *)
let export_ast file =
  let channel = open_out file in
  let lines = ref 0 in
  let line kind name id loc text =
    incr lines;
    Printf.fprintf channel "%s\t%s\t%s\t%s\t%s\n" kind name id
      (flat (range loc)) (flat text)
  in
  output_string channel "format\t2\n";
  List.iter
    (fun g ->
       let kind, name, loc, text = global_line g in
       line "global" kind name loc text;
       match g with
       | GFun (fundec, _) ->
         List.iter
           (fun stmt ->
              line "stmt" fundec.svar.vname (string_of_int stmt.sid)
                (Some (Cil_datatype.Stmt.loc stmt)) (stmt_text stmt))
           fundec.sallstmts
       | _ -> ())
    (Ast.get ()).globals;
  Printf.fprintf channel "done\t%d\n" !lines;
  close_out channel

let run () =
  Option.iter export_ast (Sys.getenv_opt "CAMPAIGN_AST_OUT");
  match Sys.getenv_opt "CAMPAIGN_QUERIES_OUT" with
  | None -> ()
  | Some file ->
    if not (Eva.Analysis.is_computed ()) then
      failwith "campaign queries: no Eva results";
    out := open_out file;
    print "format\t2\n";
    Globals.Functions.iter compute_stmt_keys;
    let functions =
      Globals.Functions.fold (fun kf acc -> kf :: acc) []
      |> List.sort (fun a b ->
          String.compare (Kernel_function.get_name a)
            (Kernel_function.get_name b))
    in
    List.iter enumerated functions;
    List.iter exit_queries functions;
    Option.iter named (Sys.getenv_opt "CAMPAIGN_QUERIES_NAMED");
    print "done\t%d\n" !count;
    close_out !out

let () = Boot.Main.extend run
