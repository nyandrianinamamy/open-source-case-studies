(* State queries of the case-study campaign.

   Loaded into Frama-C after an Eva analysis, or after [-load] of a session
   saved by one, this module writes the answers of enumerated and named state
   queries to the file named by the environment variable
   [CAMPAIGN_QUERIES_OUT]. Without that variable it does nothing.

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

   The exit queries ask, for every function whose results are available, for
   each scalar lvalue that occurs in its body, in the state at the end of the
   function ([Eva.Results.at_end_of]): its exit state. Their statement is
   written FUNCTION:exit and their point [exit].

   A query is answered only when Eva saved the results of its function
   ([Eva.Results.are_available]): with [-eva-no-results], or for a function
   analysed through its specification or a builtin, the states are not
   saved and the query is written as unavailable, never evaluated.

   Output, tab-separated:
   - [reach FUNCTION STMT] for each reached statement;
   - [answer FUNCTION STMT POINT CALLSTACK LVALUE INIT ESC VALUE] where INIT
     and ESC tell whether the value may be uninitialized or an escaping
     address, and VALUE is written as described at [value_to_string];
   - [unavailable FUNCTION STMT POINT CALLSTACK LVALUE REASON] when the state
     of the query was not saved: [no-results] when the results of the
     function are not available, [top-state] or [disabled-domain] when Eva
     returns no state for the query;
   - [error FUNCTION STMT POINT CALLSTACK LVALUE REASON] when the evaluation
     raises an exception;
   - [done COUNT] at the end, with the number of answer, unavailable and
     error lines written before it. A file without this line, or whose count
     differs, is incomplete. *)

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

(* Writes the answer of one query. [available] tells whether the results of
   the function were saved; it is checked before any evaluation, since the
   evaluation in a state that was not saved gives a top value. *)
let answer ~available ~fname ~skey point cs_key request lval_text eval =
  let point_text = point_name point in
  if not available then
    unavailable fname skey point cs_key lval_text "no-results"
  else
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

let requests stmt =
  requests_at (Eva.Results.before stmt) (Eva.Results.after stmt)

let query_stmt ~available kf stmt lvals =
  let fname = Kernel_function.get_name kf and skey = stmt_key stmt in
  List.iter
    (fun (cs_key, before, after) ->
       List.iter
         (fun (text, eval) ->
            answer ~available ~fname ~skey `Before cs_key before text eval;
            answer ~available ~fname ~skey `After cs_key after text eval)
         lvals)
    (if available then requests stmt
     else [ "*", Eva.Results.before stmt, Eva.Results.after stmt ])

let lval_query lv =
  Format.asprintf "%a" Printer.pp_lval lv, Eva.Results.eval_lval lv

let enumerated kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    let available = Eva.Results.are_available kf in
    List.iter
      (fun stmt ->
         if Eva.Results.is_reachable stmt then begin
           print "reach\t%s\t%s\n" (Kernel_function.get_name kf)
             (stmt_key stmt);
           query_stmt ~available kf stmt
             (List.map lval_query (lvals_of_stmt stmt))
         end)
      fundec.sallstmts

(* The exit queries of a function: the scalar lvalues of its body, in the
   state at the end of the function, when its results are available and its
   return statement is reached. *)
let exit_queries kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    let return = Kernel_function.find_return kf in
    if Eva.Results.are_available kf && Eva.Results.is_reachable return
    then begin
      let module S = Cil_datatype.LvalStructEq.Set in
      let lvals =
        List.fold_left (fun acc stmt -> S.union acc (S.of_list
                                                      (lvals_of_stmt stmt)))
          S.empty fundec.sallstmts
      in
      let fname = Kernel_function.get_name kf in
      let skey = fname ^ ":exit" in
      let at_end = Eva.Results.at_end_of kf in
      List.iter
        (fun (cs_key, _, request) ->
           S.iter
             (fun lv ->
                let text, eval = lval_query lv in
                answer ~available:true ~fname ~skey `Exit cs_key request text
                  eval)
             lvals)
        (requests_at at_end at_end)
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
          let available = Eva.Results.are_available kf in
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
                        answer ~available ~fname ~skey `Before cs_key before
                          text eval
                      | "after" ->
                        answer ~available ~fname ~skey `After cs_key after
                          text eval
                      | _ -> failwith ("unknown point " ^ point))
                   (if available then requests stmt
                    else [ "*", Eva.Results.before stmt,
                           Eva.Results.after stmt ]))
            stmts
        | [] | [ "" ] -> ()
        | _ -> failwith ("malformed named query: " ^ line)
      end;
      loop ()
  in
  loop ()

let run () =
  match Sys.getenv_opt "CAMPAIGN_QUERIES_OUT" with
  | None -> ()
  | Some file ->
    if not (Eva.Analysis.is_computed ()) then
      failwith "campaign queries: no Eva results";
    out := open_out file;
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
