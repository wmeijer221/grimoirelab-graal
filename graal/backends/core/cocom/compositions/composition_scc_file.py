
from graal.backends.core.analyzers.scc import SCC
from graal.backends.core.composer import Composer

SCC_FILE = 'scc_file'
CATEGORY_COCOM_SCC_FILE = 'code_complexity_' + SCC_FILE

class CompositionSccFile(Composer):
    """Analyzer Composition for Lizard Files."""

    def get_composition(self):
        return [SCC()]

    def get_category(self):
        return CATEGORY_COCOM_SCC_FILE

    def get_kind(self):
        return SCC_FILE