# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import unittest

from requests.structures import CaseInsensitiveDict
from unittest import mock

import opentelemetry as trace_api
from opentelemetry.trace import (
    INVALID_SPAN_CONTEXT,
    DEFAULT_TRACE_STATE,
    set_span_in_context,
    TraceFlags,
)
# from opentelemetry.trace.propagation.textmap import (
#     Getter,
#     Setter,
#     TextMapPropagatorT,
# )
# from opentelemetry.trace.span import INVALID_TRACE_ID
# from opentelemetry.sdk import resources, trace
from opentelemetry.sdk.extension.aws.trace import AwsXRayIdsGenerator
from opentelemetry.sdk.extension.aws.trace.propagation.aws_xray_format import (
    AWSXRayFormat
)


class AwsXRayPropagatorTest(unittest.TestCase):

    TRACE_ID_BASE16 = "8a3c60f7d188f8fa79d48a391a778fa6"

    SPAN_ID_BASE16 = "53995c3f42cd8ad8"

    carrier_setter: Setter[TextMapPropagatorT] = dict.__setitem__
    carrier_getter: Getter[TextMapPropagatorT] = dict.__getitem__
    XRAY_PROPAGATOR = AWSXRayFormat()
    # tracer = trace_api.get_tracer(__name__)

    def build_test_context(
        self,
        trace_id=TRACE_ID_BASE16,
        span_id=SPAN_ID_BASE16,
        is_remote=False,
        trace_flags=DEFAULT_TRACE_OPTIONS,
        trace_state=DEFAULT_TRACE_STATE
    ):
        return set_span_in_context(
            trace_api.DefaultSpan(span_context),
            SpanContext(
                trace_id,
                span_id,
                is_remote,
                trace_flags,
                trace_state,
            ),
        )
    
    def build_dict_with_xray_trace_header(
        self,
        trace_id=f"{AWSXRayFormat.TRACE_ID_VERSION}{TRACE_ID_DELIMITER}{TRACE_ID_BASE16[:AWSXRayFormat.TRACE_ID_FIRST_PART_LENGTH]}{AWSXRayFormat.TRACE_ID_DELIMITER}{TRACE_ID_BASE16[AWSXRayFormat.TRACE_ID_FIRST_PART_LENGTH:]}",
        span_id=SPAN_ID_BASE16,
        sampled="0",
    ):
        carrier = CaseInsentitiveDict()
        
        carrier.put({
            AWSXRayFormat.TRACE_HEADER_KEY : (
                f"{AWSXRayFormat.TRACE_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{trace_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                f"{AWSXRayFormat.PARENT_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{span_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                f"{AWSXRayFormat.SAMPLED_FLAG_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{sampled}"
            )
        })

        return carrier
    
    # Inject Tests

    def test_inject_into_non_sampled_context(self):
        carrier = CaseInsentitiveDict()
        
        XRAY_PROPAGATOR.inject(
            carrier_setter,
            carrier,
            build_test_context()
        )
        
        self.assertDictContainsSubset(
            build_dict_with_xray_trace_header(sampled="1"),
            carrier,
            'Failed to inject into context that was not yet sampled'
        )

    def test_inject_into_sampled_context(self):
        carrier = CaseInsentitiveDict()
        
        XRAY_PROPAGATOR.inject(
            carrier_setter,
            carrier,
            build_test_context(trace_flags=TraceFlags(TraceFlags.SAMPLED))
        )
        
        self.assertDictContainsSubset(
            build_dict_with_xray_trace_header(sampled="1"),
            carrier,
            'Failed to inject into context that was already sampled'
        )
    
    def test_inject_into_context_with_non_default_state(self):
        carrier = CaseInsentitiveDict()
        
        XRAY_PROPAGATOR.inject(
            carrier_setter,
            carrier,
            build_test_context(trace_state=TraceState({"foo" : "bar"}))
        )
        
        # TODO: (NathanielRN) Assert trace state when the propagator supports it
        self.assertDictContainsSubset(
            build_dict_with_xray_trace_header(sampled="1"),
            carrier,
            'Failed to inject into context with non default state'
        )

    # Extract Tests

    def get_extracted_span_context(self, encompassing_context):
        return trace.get_current_span(
            encompassing_context
        ).get_current_span_context()

    def test_extract_empty_carrier_from_none_carrier(self):

        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            CaseInsensitiveDict()
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            None
        )

    def test_extract_empty_carrier_from_invalid_context(self):

        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            CaseInsensitiveDict(),
            INVALID_SPAN_CONTEXT
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_sampled_context(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            build_test_context()
        )

    def test_extract_sampled_context(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(sampled="1"),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            build_test_context(trace_flags=TraceFlags(TraceFlags.SAMPLED))
        )

    def test_extract_different_order(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            CaseInsensitiveDict({
                AWSXRayFormat.TRACE_HEADER_KEY : (
                    f"{AWSXRayFormat.PARENT_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{span_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                    f"{AWSXRayFormat.SAMPLED_FLAG_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}0"
                    f"{AWSXRayFormat.TRACE_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{trace_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                )
            }),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            build_test_context()
        )
    
    def test_extract_with_additional_fields(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            CaseInsensitiveDict({
                AWSXRayFormat.TRACE_HEADER_KEY : (
                    f"{AWSXRayFormat.TRACE_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{trace_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                    f"{AWSXRayFormat.PARENT_ID_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}{span_id}{AWSXRayFormat.KV_PAIR_DELIMITER}"
                    f"{AWSXRayFormat.SAMPLED_FLAG_KEY}{AWSXRayFormat.KEY_AND_VALUE_DELIMITER}0"
                    ";"
                    "foo:bar"
                )
            }),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            build_test_context()
        )
    
    def test_extract_invalid_xray_trace_header(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            CaseInsensitiveDict({
                AWSXRayFormat.TRACE_HEADER_KEY : ""
            }),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_trace_id(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                trace_id="abcdefghijklmnopqrstuvwxyzabcdef"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_trace_id_size(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                trace_id="1-8a3c60f7-d188f8fa79d48a391a778fa600"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )

    def test_extract_invalid_span_id(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                span_id="abcdefghijklmnop"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_span_id_size(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                span_id="53995c3f42cd8ad800"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_empty_sampled_flag(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                sampled=""
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_sampled_flag_size(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                sampled="10002"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )
    
    def test_extract_invalid_non_numeric_sampled_flag(self):
        actual_context_encompassing_extracted = XRAY_PROPAGATOR.extract(
            carrier_getter,
            build_dict_with_xray_trace_header(
                sampled="a"
            ),
        )

        self.assertEquals(
            get_extracted_span_context(actual_context_encompassing_extracted),
            INVALID_SPAN_CONTEXT
        )