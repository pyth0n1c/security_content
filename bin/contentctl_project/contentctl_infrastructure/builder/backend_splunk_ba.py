import re
from sigma.conversion.state import ConversionState
from sigma.rule import SigmaRule
from sigma.conversion.base import TextQueryBackend
from sigma.conversion.deferred import DeferredTextQueryExpression
from sigma.conditions import ConditionFieldEqualsValueExpression, ConditionOR, ConditionAND, ConditionNOT, ConditionItem
from sigma.types import SigmaCompareExpression
from sigma.exceptions import SigmaFeatureNotSupportedByBackendError
from sigma.pipelines.splunk.splunk import splunk_sysmon_process_creation_cim_mapping, splunk_windows_registry_cim_mapping, splunk_windows_file_event_cim_mapping

from bin.contentctl_project.contentctl_core.domain.entities.detection import Detection

from typing import ClassVar, Dict, List, Optional, Pattern, Tuple


class SplunkBABackend(TextQueryBackend):
    """Splunk SPL backend."""
    precedence: ClassVar[Tuple[ConditionItem, ConditionItem, ConditionItem]] = (ConditionNOT, ConditionOR, ConditionAND)
    group_expression : ClassVar[str] = "({expr})"

    or_token : ClassVar[str] = "OR"
    and_token : ClassVar[str] = "| where"
    not_token : ClassVar[str] = "NOT"
    eq_token : ClassVar[str] = "="

    field_quote: ClassVar[str] = '"'
    field_quote_pattern: ClassVar[Pattern] = re.compile("^[\w.]+$")

    str_quote : ClassVar[str] = '"'
    escape_char : ClassVar[str] = "\\"
    wildcard_multi : ClassVar[str] = "%"
    wildcard_single : ClassVar[str] = "%"
    add_escaped : ClassVar[str] = "\\"

    re_expression : ClassVar[str] = "match_regex({field}, /(?i){regex}/)=true"
    re_escape_char : ClassVar[str] = "\\"
    re_escape : ClassVar[Tuple[str]] = ('"',)

    cidr_expression : ClassVar[str] = "{value}"

    compare_op_expression : ClassVar[str] = "{field}{operator}{value}"
    compare_operators : ClassVar[Dict[SigmaCompareExpression.CompareOperators, str]] = {
        SigmaCompareExpression.CompareOperators.LT  : "<",
        SigmaCompareExpression.CompareOperators.LTE : "<=",
        SigmaCompareExpression.CompareOperators.GT  : ">",
        SigmaCompareExpression.CompareOperators.GTE : ">=",
    }

    field_null_expression : ClassVar[str] = "{field} IS NOT NULL"

    convert_or_as_in : ClassVar[bool] = False
    convert_and_as_in : ClassVar[bool] = False
    in_expressions_allow_wildcards : ClassVar[bool] = True
    field_in_list_expression : ClassVar[str] = "{field} {op} ({list})"
    or_in_operator : ClassVar[Optional[str]] = "IN"
    list_separator : ClassVar[str] = ", "

    unbound_value_str_expression : ClassVar[str] = '{value}'
    unbound_value_num_expression : ClassVar[str] = '{value}'
    unbound_value_re_expression : ClassVar[str] = '{value}'

    deferred_start : ClassVar[str] = " "
    deferred_separator : ClassVar[str] = " OR "
    deferred_only_query : ClassVar[str] = "*"

    wildcard_match_expression : ClassVar[Optional[str]] = "like({field}, {value})"


    def __init__(self, processing_pipeline: Optional["sigma.processing.pipeline.ProcessingPipeline"] = None, collect_errors: bool = False, min_time : str = "-30d", max_time : str = "now", detection : Detection = None, **kwargs):
        super().__init__(processing_pipeline, collect_errors, **kwargs)
        self.min_time = min_time or "-30d"
        self.max_time = max_time or "now"
        self.detection = detection

    def finalize_query_data_model(self, rule: SigmaRule, query: str, index: int, state: ConversionState) -> str:

        try:
            fields = state.processing_state["fields"]
        except KeyError:
            raise SigmaFeatureNotSupportedByBackendError("No fields specified by processing pipeline")

        # fields_input_parsing = ''
        # for count, value in enumerate(fields):
        #     fields_input_parsing = fields_input_parsing + value + '=ucast(map_get(input_event, "' + value + '"), "string", null)'
        #     if not count == len(fields) - 1:
        #         fields_input_parsing = fields_input_parsing + ', '

        return f"""| where {query} """

    def finalize_output_data_model(self, queries: List[str]) -> List[str]:
        return queries