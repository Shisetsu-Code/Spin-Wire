"""Compatible exports; implementations load only when requested."""
from tester_spin.providers.base import ProviderAdapter,ProviderRegistry
from tester_spin.providers.registry import PROVIDERS,provider_class

__all__=['ProviderAdapter','ProviderRegistry']+[value[1] for value in PROVIDERS.values()]

def __getattr__(name):
 for key,(_,class_name,_) in PROVIDERS.items():
  if class_name==name:
   value=provider_class(key);globals()[name]=value;return value
 raise AttributeError(name)

def __dir__():return sorted(set(globals())|set(__all__))
