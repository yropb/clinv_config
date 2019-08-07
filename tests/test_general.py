#!/usr/bin/env python3

# import pytest

from clinv_config import (
    BlankOption, BlankOptionProvider, OptionProxy, GroupOptionProxy,
    EnumGroupOptionProxy, WrapperMeta, GroupWrapperOptionProxy)


def test_testing():
    assert 1 == 1


def test_blank_option():

    class SomeOption(BlankOption):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    new_opt = SomeOption()

    assert isinstance(new_opt, BlankOption)


def test_base_blank_option_creation():
    # Test the blank option creation e.g. if we create an option that is not
    # itself an option, but just holds options inside
    class TestOptionProvider(BlankOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

    new_option_provider = TestOptionProvider()

    assert hasattr(new_option_provider, 'option_provider')
    assert hasattr(new_option_provider, 'serialize_opt')


def test_option_provider_with_base_schema():

    class TestOptionProvider(BlankOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

            self.test_int_option = OptionProxy(
                default=1, validator=lambda x: int(x),
                option_provider=self.option_provider,
                wrapped_type=int, option_name='test_int_option')

    new_option_provider = TestOptionProvider()

    assert new_option_provider.test_int_option == 1

    assert isinstance(new_option_provider.test_int_option, int)

    assert OptionProxy.serialize_options_from(new_option_provider) == {
        'test_int_option': 1}

    class AnotherOptionProvider(TestOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

            self.test_float_option = OptionProxy(
                default=8.1, validator=lambda x: float(x),
                option_provider=self.option_provider,
                wrapped_type=float, option_name='test_float_option')

    an_option_provider = AnotherOptionProvider()

    assert an_option_provider.test_int_option == 1
    assert an_option_provider.test_float_option == 8.1

    assert OptionProxy.serialize_options_from(an_option_provider) == {
        'test_int_option': 1, 'test_float_option': 8.1}


def test_option_provider_with_composite_options():

    class TestOptionProvider(BlankOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

            self.test_int_option = OptionProxy(
                default=1, validator=lambda x: int(x),
                option_provider=self.option_provider,
                wrapped_type=int, option_name='test_int_option')

            self.comp_opt_proxy = GroupOptionProxy(
                default=dict(), validator=lambda x: dict(x),
                option_provider=self.option_provider,
                option_name='comp_opt_proxy', group_name='comp_proxy')

    new_option_provider = TestOptionProvider()

    assert OptionProxy.serialize_options_from(new_option_provider) == {
        'test_int_option': 1, 'comp_opt_proxy': {}}

    class AnotherOptionProvider(TestOptionProvider):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.test_int_internal_option = OptionProxy(
                default=4, validator=lambda x: int(x),
                option_provider=self.comp_opt_proxy,
                wrapped_type=int, option_name='test_int_internal',
                class_name='comp_proxy')

    an_option_provider = AnotherOptionProvider()

    assert an_option_provider.test_int_internal_option == 4

    assert OptionProxy.serialize_options_from(an_option_provider) == {
        'test_int_option': 1, 'comp_opt_proxy': {
            'test_int_internal': 4}}


def test_option_provider_with_enum_group():

    import enum

    class TestEnum(enum.Enum):
        ENUM1 = 1
        ENUM2 = 2
        ENUM3 = 3

    class TestOptionProvider(BlankOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

            self.enum_opt_proxy = EnumGroupOptionProxy(
                default=dict(), enum=TestEnum, validator=lambda x: dict(x),
                option_provider=self.option_provider,
                option_name='test_enum_proxy')

    new_option_provider = TestOptionProvider()

    assert new_option_provider.enum_opt_proxy.serialize_opt(new_option_provider) == dict()

    an_option_provider = TestOptionProvider(
        option_provider=dict(
            test_enum_proxy={
                1: 'test1',
                2: 'test2'}))

    assert an_option_provider.enum_opt_proxy.serialize_opt(an_option_provider) == {
        1: 'test1', 2: 'test2'}

    assert TestEnum.ENUM1 in an_option_provider.enum_opt_proxy
    assert TestEnum.ENUM2 in an_option_provider.enum_opt_proxy
    assert TestEnum.ENUM3 not in an_option_provider.enum_opt_proxy


def test_option_provider_with_wrapper_proxy():

    class WrapCls(WrapperMeta):
        def __init__(self, *, to_wrap: int):
            self.wrapped = to_wrap

        def serialize_opt(self, cls_woptions):
            return self.wrapped

    class TestOptionProvider(BlankOptionProvider):
        def __init__(self, option_provider=dict()):
            super().__init__(option_provider=option_provider)

            self.group_wrapper = GroupWrapperOptionProxy(
                default=dict(), wrapper_cls=WrapCls, validator=lambda x: x,
                option_provider=self.option_provider, option_name='group_wrapper')

    new_option_provider = TestOptionProvider()

    assert isinstance(new_option_provider.group_wrapper, dict)

    new_option_provider = TestOptionProvider(
        option_provider=dict(
            group_wrapper=dict(
                someval=23,
                anotherval=2323)))

    assert 'someval' in new_option_provider.group_wrapper
    assert isinstance(new_option_provider.group_wrapper.get(
        'someval'), WrapCls)

    assert OptionProxy.serialize_options_from(
        new_option_provider) == {
            'group_wrapper': {
                'someval': 23,
                'anotherval': 2323}}
