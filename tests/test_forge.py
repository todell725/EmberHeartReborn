from engines.forge_engine import ForgeEngine

def test_forge_engine_init():
    engine = ForgeEngine()
    assert engine is not None
    assert type(engine.active_projects) == dict
