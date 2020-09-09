from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base

from logic_engine.exec_trans_logic.listeners import before_flush
from logic_engine.rule_bank import rule_bank_withdraw
from logic_engine.rule_bank.rule_bank import RuleBank
from nw.nw_logic import session


def setup(a_session: session, an_engine: Engine):
    rules_bank = RuleBank()
    rules_bank._session = a_session
    event.listen(a_session, "before_flush", before_flush)
    rules_bank._tables = {}
    rules_bank._at = datetime.now()

    rules_bank._engine = an_engine
    rules_bank._rb_base = declarative_base  # FIXME good grief, not appearing, no error
    return


def validate_formula_dependencies(class_name: str):
    """
    compute formula._exec_order
    """
    formula_list = rule_bank_withdraw.get_formula_rules(class_name)
    formula_list_dict = {}
    for each_formula in formula_list:
        formula_list_dict[each_formula._column] = each_formula
    exec_order = 0
    blocked = False
    while not blocked and exec_order < len(formula_list):
        blocked = True
        for each_formula_name in formula_list_dict:
            each_formula = formula_list_dict[each_formula_name]
            refers_to = ""
            if each_formula._exec_order == -1:
                for each_referenced_col_name in each_formula._dependencies:
                    if each_referenced_col_name in formula_list_dict:
                        referenced_formula = formula_list_dict[each_referenced_col_name]
                        if referenced_formula._exec_order == -1:  # ref'd col done?
                            refers_to = referenced_formula._column
                            break  # can't do me yet - ref'd col not done
                if refers_to == "":
                    exec_order += 1
                    each_formula._exec_order = exec_order
                    blocked = False
        if blocked:
            cycles = ""
            cycle_count = 0
            for each_formula_name in formula_list_dict:
                each_formula = formula_list_dict[each_formula_name]
                if each_formula._exec_order == -1:
                    if cycle_count > 0:
                        cycles += ", "
                    cycle_count += 1
                    cycles += each_formula._column
            raise Exception("blocked by circular dependencies: " + cycles)


def validate(a_session: session, engine: Engine):
    list_rules = "\n\nValidate Rule Bank"
    rules_bank = RuleBank()

    formula_list = []
    for each_key in rules_bank._tables:
        validate_formula_dependencies(class_name=each_key)
    list_rules += rules_bank.__str__()
    print(list_rules)
    return True

