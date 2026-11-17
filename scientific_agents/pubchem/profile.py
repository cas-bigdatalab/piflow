"""Only application identity and capability selection; no execution pipeline."""
from ..agent_profiles import AgentProfile, ToolScope


PROFILE = AgentProfile(
    agent_id="pubchem", label="PubChem 化合物助手",
    resource_noun="化合物",
    instructions=(
        "Help users retrieve and analyze PubChem compounds and export saved results. "
        "Use the available tool schemas and result contracts for supported operations, "
        "parameters and completion criteria. Preserve the user's molecular structure, "
        "numeric conditions and requested output format. Explain capabilities outside "
        "this assistant's scope without claiming the entire platform lacks them."
    ),
    tool_scope=(ToolScope("piflow-corpus", groups=("pubchem",), tools=("export_dataset",)),),
)
