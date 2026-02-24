from engines.tick_engine import TickEngine

def test_tick_engine_init():
    engine = TickEngine()
    assert engine is not None
