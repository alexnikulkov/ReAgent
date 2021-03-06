#!/usr/bin/env python3

import abc
import logging
from typing import Dict, Optional, Type

from reagent.core.dataclasses import dataclass
from reagent.core.tagged_union import INTERNAL_TAGGED_UNION, TaggedUnion


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RegistryMeta(abc.ABCMeta):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, "REGISTRY"):
            # Put REGISTRY on cls. This only happens once on the base class
            logger.debug("Adding REGISTRY to type {}".format(name))
            cls.REGISTRY: Dict[str, Type] = {}
            cls.REGISTRY_NAME = name
            cls.REGISTRY_FROZEN = False

        assert not cls.REGISTRY_FROZEN, (
            f"{cls.REGISTRY_NAME} has been used to fill a union. "
            "Please rearrange your import orders"
        )

        if not cls.__abstractmethods__ and name != cls.REGISTRY_NAME:
            # Only register fully-defined classes
            if hasattr(cls, "__registry_name__"):
                registry_name = cls.__registry_name__
                logger.info(
                    f"Registering {name} with alias {registry_name} to {cls.REGISTRY_NAME}"
                )
                name = registry_name
            else:
                logger.info(f"Registering {name} to {cls.REGISTRY_NAME}")
            # assert name not in cls.REGISTRY
            # TODO: Combine FB and OSS model managers and then bring back this assert.
            # For now this works because FB model managers inherit from their OSS counterparts
            if name in cls.REGISTRY:
                logger.warning(f"Overwriting open source {name} with internal version")
            cls.REGISTRY[name] = cls
        else:
            logger.info(
                f"Not Registering {name} to {cls.REGISTRY_NAME}. Abstract "
                f"method {list(cls.__abstractmethods__)} are not implemented."
            )
        return super().__init__(name, bases, attrs)

    def fill_union(cls):
        def wrapper(union):
            cls.REGISTRY_FROZEN = True

            def make_union_instance(inst, instance_class=None):
                inst_class = instance_class or type(inst)
                key = getattr(inst_class, "__registry_name__", inst_class.__name__)
                return union(**{key: inst})

            union.make_union_instance = make_union_instance

            if not INTERNAL_TAGGED_UNION:
                # OSS TaggedUnion
                union.__annotations__ = {
                    name: Optional[t] for name, t in cls.REGISTRY.items()
                }
                for name in cls.REGISTRY:
                    setattr(union, name, None)
                return dataclass(frozen=True)(union)
            else:
                # FBL TaggedUnion
                union.__annotations__ = {name: t for name, t in cls.REGISTRY.items()}
                return union

        return wrapper
