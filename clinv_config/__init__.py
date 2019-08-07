#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Optional
from wrapt import ObjectProxy
# from enum import Enum


class BlankOption:
    ''' This is a base Option class, without object proxies,
    as it actually does not have to proxy any attributes or methods.
    If we want to have any options to be straight proxied, we have to
    inherit from both BlankOption and ObjectProxy '''

    @staticmethod
    def serialize_options_from(
            inst, option_group: Optional[str] = None) -> dict:
        ''' This static method provides an ability to go over
        any object and gather any provided options into dict.
        By default the root of the dictionary should be represented
        by option_group `None`, without string name '''
        serialized_dict = dict()

        for _, itm in inst.__dict__.items():
            if isinstance(
                itm, BlankOption) and (
                    itm._self_option_group == option_group):
                serialized_dict[itm._self_option_name] = itm.serialize_opt(
                    inst)
        return serialized_dict

    def __init__(
            self, *args,
            parent_option: Optional['BlankOption'] = None,
            option_provider: Optional[dict] = None,
            **kwargs) -> None:
        ''' As this BlankOption class can be used as mixin class for any other
        class, we use only keyword arguments to avoid messing with positional
        ones '''
        self.parent_option = parent_option
        self.option_provider = option_provider
        super().__init__(*args, **kwargs)

    def serialize_opt(self, parent_inst):
        ''' Here we serialize the option that is contained inside '''
        raise NotImplementedError(
            'This method should be overriden in subclasses')

    def gather_options(self):
        ''' Here we gather all options contained inside '''
        raise NotImplementedError(
            'This method should be overriden in subclasses')

    def process_options(self, options):
        ''' Here we process gathered options and produce the final result '''
        raise NotImplementedError(
            'This method should be overriden is subclasses')


class BlankOptionProvider(BlankOption):
    ''' This is a base option provider - itself it's not an option,
    but can hold other options and should be able to serialize them back into
    dictionary as requested '''

    def __init__(
        self, *args,
        option_provider: dict = dict(),
        **kwargs) -> None:
        ''' Here we grab an option_provider that is a blank dictionary
        by default, but in general we have to supply a proper provider
        that will be properly parsed and stripped into provided parts '''
        super().__init__(*args, option_provider=option_provider, **kwargs)


class OptionProxy(ObjectProxy):

    @staticmethod
    def get_options(cls_woptions, option_class=None):
        opt_dct = dict()
        for name, itm in cls_woptions.__dict__.items():
            if isinstance(itm, OptionProxy):
                opt_dct[name] = (itm, itm.__wrapped__, itm._self_option_name)

        return opt_dct

    @staticmethod
    def serialize_options_from(cls_woptions, class_name=None):
        serialized_dct = dict()
        for _, itm in cls_woptions.__dict__.items():
            if isinstance(
                    itm, OptionProxy) and itm._self_class_name == class_name:
                serialized_dct[itm._self_option_name] = itm.serialize_opt(
                    cls_woptions)
        return serialized_dct

    def __init__(
        self, *, default, validator, option_provider, wrapped_type,
        option_name, group_name=None, class_name=None):
        super().__init__(default)
        self._self_option_loaded = False
        self._self_option_changed = False
        self._self_default = default
        self._self_wrapped_type = wrapped_type
        self._self_option_name = option_name
        self._self_option_provider = option_provider
        self._self_group_name = group_name
        self._self_class_name = class_name
        try:
            if option_name in self._self_option_provider:
                self.__wrapped__ = validator(
                    self._self_option_provider.get(option_name))
                self._self_option_loaded = True
        except:
            pass

    def serialize_opt(self, cls_woptions):
        return self.__wrapped__

    @property
    def _option_loaded(self):
        return self._self_option_loaded

    @property
    def _option_changed(self):
        return self._self_option_changed

    def __reduce_ex__(self, protocol):
        return type(self.__wrapped__), (self.__wrapped__,)


class FloatOptionProxy(OptionProxy):
    ''' This is an option proxy that handles float point options '''

    def __init__(self, default_val, option_name, conf_dict, **kwargs):
        super().__init__(default_val, float, option_name, conf_dict, **kwargs)


class IntOptionProxy(OptionProxy):
    ''' This is an option proxy that handles int options '''

    def __init__(self, default_val, option_name, conf_dict, **kwargs):
        super().__init__(default_val, int, option_name, conf_dict, **kwargs)


class StrOptionProxy(OptionProxy):
    ''' This is an option proxy that handles str options '''

    def __init__(self, default_val, option_name, conf_dict, **kwargs):
        super().__init__(default_val, str, option_name, conf_dict, **kwargs)


class GroupOptionProxy(OptionProxy):
    ''' This is an option proxy that handles subgroups of options,
    like an option that is represented by a dictionary that contains
    other options that we also want to use, and also want to be able
    to save configuration in it's original schema '''

    def __init__(
        self, *, default, validator, option_provider,
        option_name, group_name, class_name=None):
        super().__init__(
            default=default, validator=validator,
            option_provider=option_provider, wrapped_type=dict,
            option_name=option_name, group_name=group_name, class_name=class_name)

    def serialize_opt(self, cls_woptions):
        return OptionProxy.serialize_options_from(
            cls_woptions, class_name=self._self_group_name)


class WrapperMeta(ABC):
    ''' This is an abstract base class for all proxy wrappers '''

    def __init__(self, *args, to_wrap, **kwargs):
        pass

    @abstractmethod
    def serialize_opt(self, cls_woptions: BlankOptionProvider):
        pass


class GroupWrapperOptionProxy(OptionProxy):
    ''' This is an option proxy that is a virtual group proxy, but inside
    it wraps every item in a provided class, using two provided callbacks
    to upconvert and downconvert a result object back to it's original state '''

    def __init__(
        self, *, default: dict, wrapper_cls: WrapperMeta, validator,
        option_provider: dict, option_name: str, group_name=None, class_name=None):
        super().__init__(
            default=default, validator=validator,
            option_provider=option_provider, wrapped_type=dict,
            option_name=option_name, group_name=group_name,
            class_name=class_name)
        self._self_wrapper_cls = wrapper_cls
        wrapped_copy = self.__wrapped__.copy()
        self.__wrapped__ = dict()
        for key, value in wrapped_copy.items():
            try:
                self.__wrapped__[key] = self._self_wrapper_cls(to_wrap=value)
            except:
                pass

    def serialize_opt(self, cls_woptions):
        opt_serialized = dict()
        for key, value in self.__wrapped__.items():
            opt_serialized[key] = value.serialize_opt(cls_woptions)
        return opt_serialized


class EnumGroupOptionProxy(OptionProxy):
    ''' This is an option proxy that handles a group of options,
    but instead of straight proxying the internal values '''

    def __init__(
        self, *, default: dict, enum, validator, option_provider: dict,
        option_name: str, group_name=None, class_name=None):
        super().__init__(
            default=default, validator=validator,
            option_provider=option_provider, wrapped_type=dict,
            option_name=option_name, group_name=group_name,
            class_name=class_name)
        self._self_wrapped_enum = enum
        wrapped_copy = self.__wrapped__.copy()
        self.__wrapped__ = dict()
        for key, value in wrapped_copy.items():
            try:
                self.__wrapped__[enum(key)] = value
            except ValueError:
                pass

    def serialize_opt(self, cls_woptions):
        opt_serialized = dict()
        for key, value in self.__wrapped__.items():
            opt_serialized[key.value] = value
        return opt_serialized


class ListOptionProxy(OptionProxy):
    ''' This is an option proxy that handles a group of options,
    but instead of GroupOptionProxy, the wrapped option is a list,
    and list that can contain only one type, as each option will
    be wrapped in provided OptionProxy class, so we could track all
    changes to each member in the future '''

    def __init__(
        self, default_val: list, option_name: str, conf_dict: dict,
        group_name: str, class_name: str,
        wrapper_type: OptionProxy) -> None:
        ''' Here the wrapper_type represents the option proxy '''
        pass
