from engines.slayer_engine import SlayerEngine

def test_slayer_engine_init():
    engine = SlayerEngine()
    assert engine is not None
    assert type(engine.active_tasks) == dict
