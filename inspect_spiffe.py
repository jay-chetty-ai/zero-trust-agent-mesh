
from spiffe import X509Source
import logging

# We need a dummy source or similar, but X509Bundle can be instantiated directly if we import it.
from spiffe import X509Bundle

print("X509Bundle methods:", dir(X509Bundle))
# help(X509Bundle.x509_authorities)

import inspect
print(inspect.signature(X509Bundle.__init__))
