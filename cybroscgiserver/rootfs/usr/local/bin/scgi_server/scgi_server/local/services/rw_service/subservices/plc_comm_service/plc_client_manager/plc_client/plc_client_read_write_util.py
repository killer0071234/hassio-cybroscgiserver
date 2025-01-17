from dataclasses import dataclass
from itertools import chain
from typing import List, Tuple, Iterable, Union, Optional

from scgi_server.local.general.misc import split_at_index
from scgi_server.local.input_output.abus_stack.abus.command_frame import CommandFrameUtil
from scgi_server.local.input_output.abus_stack.abus.transport_frame import \
    TransportFrameUtil
from scgi_server.local.services.rw_service.subservices.plc_comm_service.data_type import \
    DataType

RParams = Tuple[
    List[int],
    List[int],
    List[int],
    List[DataType]
]

RResults = Tuple[Iterable[int], Iterable[int], Iterable[Union[int, float]]]

WParams = Tuple[
    List[int],
    List[int],
    List[int],
    List[int],
    List[int],
    List[Union[int, float]],
    List[DataType]
]


@dataclass(frozen=True)
class PlcClientReadWriteUtil:
    TRANSPORT_LAYER_AND_COMMAND_HEAD_AND_COMMAND = \
        TransportFrameUtil.HEADER_LENGTH + \
        TransportFrameUtil.TRANSACTION_ID_LENGTH + \
        TransportFrameUtil.CRC_LENGTH + \
        CommandFrameUtil.HEAD_LENGTH + \
        CommandFrameUtil.COMMAND_LENGTH

    max_frame_size: int

    @property
    def _max_params_length(self) -> int:
        return (self.max_frame_size -
                self.TRANSPORT_LAYER_AND_COMMAND_HEAD_AND_COMMAND)

    def split_r_random_memory_params(
        self,
        params: Tuple[List[int], List[int], List[int], List[int]]
    ) -> Tuple[
        Tuple[List[int], List[int], List[int], List[int]],
        Optional[Tuple[List[int], List[int], List[int], List[int]]]
    ]:
        one_b_addrs, two_b_addrs, four_b_addrs, four_b_types = params

        available_req_size = self._max_params_length - (3 * 2)
        available_res_size = self._max_params_length

        (
            one_b_addrs_to_use,
            one_b_addrs_left,
            available_req_size,
            available_res_size
        ) = self._split_r_addrs(
            one_b_addrs,
            2,
            1,
            available_req_size,
            available_res_size
        )
        if len(one_b_addrs_left) > 0:
            params_to_use: Tuple[
                List[int], List[int], List[int], List[int]
            ] = one_b_addrs_to_use, [], [], []
            params_left = (
                one_b_addrs_left,
                two_b_addrs,
                four_b_addrs,
                four_b_types
            )
            return params_to_use, params_left

        (
            two_b_addrs_to_use,
            two_b_addrs_left,
            available_req_size,
            available_res_size
        ) = self._split_r_addrs(
            two_b_addrs,
            2,
            2,
            available_req_size,
            available_res_size
        )
        if len(two_b_addrs_left) > 0:
            params_to_use = one_b_addrs_to_use, two_b_addrs_to_use, [], []
            params_left = (
                one_b_addrs_left,
                two_b_addrs_left,
                four_b_addrs,
                four_b_types
            )
            return params_to_use, params_left

        (
            four_b_addrs_to_use,
            four_b_addrs_left,
            available_req_size,
            available_res_size
        ) = self._split_r_addrs(
            four_b_addrs,
            2,
            4,
            available_req_size,
            available_res_size
        )
        (
            four_b_types_to_use,
            four_b_types_left
        ) = split_at_index(four_b_types, len(four_b_addrs_to_use))

        params_to_use = (
            one_b_addrs_to_use,
            two_b_addrs_to_use,
            four_b_addrs_to_use,
            four_b_types_to_use
        )

        if len(four_b_addrs_left) > 0:
            params_left = (
                one_b_addrs_left,
                two_b_addrs_left,
                four_b_addrs_left,
                four_b_types_left
            )
            return params_to_use, params_left

        return params_to_use, None

    @staticmethod
    def _split_r_addrs(
        addrs: List[int],
        addr_contribution_to_req_size: int,
        addr_contribution_to_res_size: int,
        available_req_size: int,
        available_res_size: int,
    ) -> Tuple[List[int], List[int], int, int]:
        max_fit_count_regarding_req = \
            available_req_size // addr_contribution_to_req_size

        max_fit_count_regarding_res = \
            available_res_size // addr_contribution_to_res_size

        max_fit_count = min(max_fit_count_regarding_req,
                            max_fit_count_regarding_res)

        addrs_that_fit, rest_of_addrs = split_at_index(addrs, max_fit_count)
        fit_count = len(addrs_that_fit)
        return (
            addrs_that_fit,
            rest_of_addrs,
            available_req_size - (fit_count * addr_contribution_to_req_size),
            available_res_size - (fit_count * addr_contribution_to_res_size),
        )

    @staticmethod
    def merge_r_random_memory_results(
        r1: Tuple[List[int], List[int], List[int]],
        r2: Tuple[Tuple[int, ...], Tuple[int, ...], List[int]]
    ) -> Tuple[Iterable[int], Iterable[int], Iterable[int]]:
        one_b_values1, two_b_values1, four_b_values1 = r1
        one_b_values2, two_b_values2, four_b_values2 = r2

        return (
            chain(one_b_values1, one_b_values2),
            chain(two_b_values1, two_b_values2),
            chain(four_b_values1, four_b_values2)
        )

    def split_w_random_memory_params(
        self,
        params: Tuple[
            List[int], List[int], List[int],
            List[int], List[Union[int, float, None]], List[
                Union[int, float, None]
            ],
            List[DataType]
        ]
    ) -> Tuple[
        Tuple[
            List[int], List[int], List[int],
            List[int], List[Union[int, float, None]], List[
                Union[int, float, None]
            ],
            List[DataType]
        ],
        Optional[Tuple[
            List[int], List[int], List[int],
            List[int], List[Union[int, float, None]], List[
                Union[int, float, None]
            ],
            List[Optional[DataType]]
        ]]
    ]:
        (
            one_b_addrs,
            two_b_addrs,
            four_b_addrs,
            one_b_values,
            two_b_values,
            four_b_values,
            four_b_types
        ) = params

        available_req_size = self._max_params_length - 3

        (
            one_b_addrs_to_use,
            one_b_addrs_left,
            one_b_values_to_use,
            one_b_values_left,
            available_req_size
        ) = self._split_w_addrs_and_values(
            one_b_addrs,
            one_b_values,
            2,
            1,
            available_req_size
        )
        if len(one_b_addrs_left) > 0:
            params_to_use: Tuple[
                List[int], List[int], List[int],
                List[int], List[Union[int, float, None]], List[
                    Union[int, float, None]
                ],
                List[DataType]
            ]
            params_to_use = (
                one_b_addrs_to_use, [], [],
                one_b_values_to_use, [], [],
                []
            )
            params_left = (
                one_b_addrs_left,
                two_b_addrs,
                four_b_addrs,
                one_b_values_left,
                two_b_values,
                four_b_values,
                four_b_types
            )
            return params_to_use, params_left

        (
            two_b_addrs_to_use,
            two_b_addrs_left,
            two_b_values_to_use,
            two_b_values_left,
            available_req_size
        ) = self._split_w_addrs_and_values(
            two_b_addrs,
            two_b_values,
            2,
            2,
            available_req_size
        )
        if len(two_b_addrs_left) > 0:
            params_to_use: Tuple[
                List[int], List[int], List[int],
                List[int], List[Union[int, float, None]], List[
                    Union[int, float, None]
                ],
                List[DataType]
            ]
            params_to_use = (
                one_b_addrs_to_use, two_b_addrs_to_use, [],
                one_b_values_to_use, two_b_values_to_use, [],
                []
            )
            params_left = (
                one_b_addrs_left,
                two_b_addrs_left,
                four_b_addrs,
                one_b_values_left,
                two_b_values_left,
                four_b_values,
                four_b_types
            )
            return params_to_use, params_left

        (
            four_b_addrs_to_use,
            four_b_addrs_left,
            four_b_values_to_use,
            four_b_values_left,
            available_req_size
        ) = self._split_w_addrs_and_values(
            four_b_addrs,
            four_b_values,
            2,
            4,
            available_req_size
        )

        (four_b_types_to_use, four_b_types_left) = split_at_index(
            four_b_types,
            len(four_b_addrs_to_use)
        )

        params_to_use = (
            one_b_addrs_to_use, two_b_addrs_to_use, four_b_addrs_to_use,
            one_b_values_to_use, two_b_values_to_use, four_b_values_to_use,
            four_b_types_to_use
        )
        if len(four_b_addrs_left) > 0:
            params_left = (
                one_b_addrs_left,
                two_b_addrs_left,
                four_b_addrs_left,
                one_b_values_left,
                two_b_values_left,
                four_b_values_left,
                four_b_types_left
            )
            return params_to_use, params_left

        return params_to_use, None

    @staticmethod
    def _split_w_addrs_and_values(
        addrs: List[int],
        values: List[Union[int, float, None]],
        addr_contribution_to_req_size: int,
        value_contribution_to_req_size: int,
        available_req_size: int,
    ) -> Tuple[List[int], List[int], List[int], List[int], int]:
        max_fit_count = available_req_size // (
            addr_contribution_to_req_size + value_contribution_to_req_size
        )

        addrs_that_fit, rest_of_addrs = split_at_index(addrs, max_fit_count)
        values_that_fit, rest_of_values = split_at_index(values, max_fit_count)
        fit_count = len(addrs_that_fit)

        return (
            addrs_that_fit,
            rest_of_addrs,
            values_that_fit,
            rest_of_values,
            available_req_size - (fit_count * addr_contribution_to_req_size),
        )
