# app/processors/__init__.py

# This makes the processors directory a Python package
# You can leave it empty, or add imports for convenience

# Optional: Make specific classes easily importable
from .processor_router import ProcessorRouter
from .code_processor import CodeProcessor
#from .latin_rag_processor import LatinRAGProcessor
#from .latin_processor import LatinProcessor
#from .augustine_rag_processor import AugustineRAGProcessor
from .psalm_rag_processor import PsalmRAGProcessor

# This allows: from app.processors import CodeProcessor
# Instead of: from app.processors.code_processor import CodeProcessor