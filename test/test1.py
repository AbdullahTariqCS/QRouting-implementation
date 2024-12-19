import simpy
import simpy.rt
import simpy.events

def example(env: simpy.Environment):
    event = simpy.events.Timeout(env, delay=1, value=42)
    value = yield event
    print('now=%d, value=%d' % (env.now, value))

env = simpy.rt.RealtimeEnvironment(factor=1)
example_gen = example(env)
p = simpy.events.Process(env, example_gen)

env.run()
# now=1, value=42