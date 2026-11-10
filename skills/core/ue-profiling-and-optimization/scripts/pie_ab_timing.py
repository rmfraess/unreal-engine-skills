"""PIE A/B GPU timing at a fixed camera (UE 5.8 + VibeUE PerformanceService).

Run inside execute_python_code:
    exec(open(PATH).read())
    pie_ab(configs, cam=(x, y, z, pitch, yaw), out='C:/.../pie_ab.json')
then poll for the JSON from a separate call (the run is tick-driven; never sleep in the Editor).

configs: list of tuples (label, cvars, hide, props)
    cvars: {'r.Some.CVar': value}
    hide:  name substrings; matching ISM/HISM/InstancedSkinned components are hidden
    props: {'editor_property': (name_substrings, value)} set on matching components
All changes touch the PIE world only; cvars and props are restored after each config and at the end.
Start with a 'warmup' config and repeat the baseline at the end: single runs carry about +/-0.7 ms noise.
Call unreal.PerformanceService.set_background_throttling(False) first, and re-enable it afterwards.
"""
import unreal, os, json, time, statistics

INSTANCED = ('InstancedStaticMeshComponent', 'HierarchicalInstancedStaticMeshComponent', 'InstancedSkinnedMeshComponent')


def pie_ab(configs, cam, out, settle=10.0, frames=45):
    x, y, z, pitch, yaw = cam
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    st = {'i': -1, 't': 0.0, 'gpu': [], 'gt': [], 'res': {}, 'start': time.time(), 'cv': {}, 'orig': {}}
    if os.path.exists(out):
        os.remove(out)
    unreal.PerformanceService.start_pie()

    def restore(w):
        for cv, v in st['cv'].items():
            unreal.SystemLibrary.execute_console_command(w, f'{cv} {v}')
        for (c, prop), v in st['orig'].items():
            c.set_editor_property(prop, v)

    def finish(w):
        restore(w)
        json.dump(st['res'], open(out, 'w'), indent=1)
        unreal.PerformanceService.stop_pie()
        unreal.unregister_slate_post_tick_callback(st['h'])

    def apply(w, cfg):
        restore(w)
        _, cvars, hide, props = (tuple(cfg) + ({}, (), {}))[:4]
        for cv, v in cvars.items():
            st['cv'].setdefault(cv, unreal.SystemLibrary.get_console_variable_float_value(cv))
            unreal.SystemLibrary.execute_console_command(w, f'{cv} {v}')
        for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            for c in a.get_components_by_class(unreal.SceneComponent):
                tn = type(c).__name__
                if tn not in INSTANCED:
                    continue
                m = c.get_editor_property('skinned_asset' if tn == 'InstancedSkinnedMeshComponent' else 'static_mesh')
                n = m.get_name() if m else ''
                c.set_visibility(not (n and any(h in n for h in hide)))
                for prop, (match, v) in props.items():
                    if n and any(k in n for k in match):
                        st['orig'].setdefault((c, prop), c.get_editor_property(prop))
                        c.set_editor_property(prop, v)

    def tick(dt):
        w = ues.get_game_world()
        if w is None:
            if time.time() - st['start'] > 120:
                st['res']['error'] = 'PIE did not start'
                json.dump(st['res'], open(out, 'w'))
                unreal.unregister_slate_post_tick_callback(st['h'])
            return
        unreal.SystemLibrary.execute_console_command(w, f'BugItGo {x} {y} {z} {pitch} {yaw} 0')
        now = time.time()
        if st['i'] >= 0:
            if now - st['t'] < settle:
                return
            g = json.loads(unreal.PerformanceService.frame_timing(60.0))
            if g.get('gpu_ms'):
                st['gpu'].append(g['gpu_ms'])
            if g.get('game_thread_ms'):
                st['gt'].append(g['game_thread_ms'])
            if len(st['gpu']) < frames:  # render_thread_ms reads 0 in PIE; count GPU samples
                return
            st['res'][configs[st['i']][0]] = {'gpu': round(statistics.median(st['gpu']), 2),
                                              'gt': round(statistics.median(st['gt']), 2) if st['gt'] else None}
        st['i'] += 1
        st['gpu'], st['gt'] = [], []
        if st['i'] >= len(configs):
            finish(w)
            return
        apply(w, configs[st['i']])
        st['t'] = now

    st['h'] = unreal.register_slate_post_tick_callback(tick)
