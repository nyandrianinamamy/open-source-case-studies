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

   Output, tab-separated:
   - [reach FUNCTION STMT] for each reached statement;
   - [answer FUNCTION STMT POINT CALLSTACK LVALUE INIT ESC VALUE] where INIT
     and ESC tell whether the value may be uninitialized or an escaping
     address, and VALUE is written as described at [value_to_string];
   - [error FUNCTION STMT POINT CALLSTACK LVALUE REASON] when Eva gives no
     answer;
   - [done COUNT] at the end, with the number of answers. *)

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

let answer kf stmt point cs_key request lval_text eval =
  let fname = Kernel_function.get_name kf in
  let skey = stmt_key stmt in
  let point = match point with `Before -> "before" | `After -> "after" in
  match Eva.Results.as_cvalue_or_uninitialized eval with
  | v ->
    incr count;
    let init = if Cvalue.V_Or_Uninitialized.is_initialized v then 1 else 0 in
    let esc = if Cvalue.V_Or_Uninitialized.is_noesc v then 0 else 1 in
    let value = Cvalue.V_Or_Uninitialized.get_v v in
    let value =
      if Cvalue.V.is_bottom value && Eva.Results.is_empty request
      then "B" else value_to_string value
    in
    print "answer\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%s\n"
      fname skey point cs_key lval_text init esc value
  | exception exn ->
    print "error\t%s\t%s\t%s\t%s\t%s\t%s\n" fname skey point cs_key lval_text
      (escape (Printexc.to_string exn))

let requests stmt =
  let before = Eva.Results.before stmt and after = Eva.Results.after stmt in
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

let query_stmt kf stmt lvals =
  List.iter
    (fun (cs_key, before, after) ->
       List.iter
         (fun (text, eval) ->
            answer kf stmt `Before cs_key before text (eval before);
            answer kf stmt `After cs_key after text (eval after))
         lvals)
    (requests stmt)

let lval_query lv =
  Format.asprintf "%a" Printer.pp_lval lv, Eva.Results.eval_lval lv

let enumerated kf =
  match kf.fundec with
  | Declaration _ -> ()
  | Definition (fundec, _) ->
    List.iter
      (fun stmt ->
         if Eva.Results.is_reachable stmt then begin
           print "reach\t%s\t%s\n" (Kernel_function.get_name kf)
             (stmt_key stmt);
           query_stmt kf stmt (List.map lval_query (lvals_of_stmt stmt))
         end)
      fundec.sallstmts

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
          let query = "named:" ^ var, Eva.Results.eval_var vi in
          let stmts = (Kernel_function.get_definition kf).sallstmts in
          List.iter
            (fun stmt ->
               let loc = Cil_datatype.Stmt.loc stmt in
               if Fileloc.line loc = line_no then
                 List.iter
                   (fun (cs_key, before, after) ->
                      match point with
                      | "before" ->
                        answer kf stmt `Before cs_key before (fst query)
                          (snd query before)
                      | "after" ->
                        answer kf stmt `After cs_key after (fst query)
                          (snd query after)
                      | _ -> failwith ("unknown point " ^ point))
                   (requests stmt))
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
    Option.iter named (Sys.getenv_opt "CAMPAIGN_QUERIES_NAMED");
    print "done\t%d\n" !count;
    close_out !out

let () = Boot.Main.extend run
