import yaml
from jiminy.yaml_loader import load_scenario

def test_load_yaml_basic(tmp_path):
    yaml_content = """
context:
  - id: w1
    description: "Test fact"

norms:
  - id: N1
    body: ["w1"]
    conclusion: "i1"
    type: "c"
    stakeholder: "Test"

contrariness:
  i1:
    contraries: ["d1"]
    description: "test contrariness"

priorities:
  d1:
    value: 3
    description: "test priority"
"""

    f = tmp_path / "scenario.yaml"
    f.write_text(yaml_content)

    (context, norms, contr, prio, ctx_desc, norm_desc, cdesc, pdesc, base_priorities, meta_priorities) = load_scenario(str(f))

    assert "w1" in context
    assert ctx_desc["w1"] == "Test fact"
    assert norms[0].head == "i1"
    assert contr["i1"] == {"d1"}
    assert prio["d1"] == 3
