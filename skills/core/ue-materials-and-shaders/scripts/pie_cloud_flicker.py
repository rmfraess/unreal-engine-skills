"""Volumetric-cloud grain and flicker probe for PIE (VibeUE editor Python).

Per config: run console commands, set the cloud component's view sample scale, optional layer height, parameters on
the cloud's material (a PIE MID is created first if needed, so the saved instance is never written) and component
setters such as {'tracing_max_distance': 20.0}; hold or pan the camera; grab a burst of frames with the `Shot`
console command (it keeps the cloud's temporal history; HighResShot does not); log PerformanceService.frame_timing().
Offline, report() prints grain (one-frame high-pass: the fizzy-dot look) and flicker (back-and-forth change across
the burst; steady drift scores ~0).

Editor, during PIE (copy this file onto the Editor's Python path first):
    import pie_cloud_flicker as f
    M0 = 'r.VolumetricRenderTarget.Mode 0'
    view = ((-50883, 99267, 116193), (20.2, 99.6))      # (location cm, (pitch, yaw)): the user's camera if known
    still = {'Cloud_Wind_mps': 0.0}                         # freeze drift so every config sees the same sky
    f.start('spk', [('t50', [M0], 3.0, None, still, {'tracing_max_distance': 50.0}),
                    ('t20', [M0], 3.0, None, still, {'tracing_max_distance': 20.0}),
                    ('t50b', [M0], 3.0, None, still, {'tracing_max_distance': 50.0})],  # repeated baseline
            view, frames=8)
    f.start('slow', configs, view, frames=40, every_s=0.1)  # popping over ~4 s
    f.start('pan', configs, view, settle=3.0, pan_dps=4.0)  # motion: judge the crops by eye
    # A/B against Epic's own puffy sky on the same MID (zero your custom coverage parameters as well):
    #   ('epic', [M0], 3.0, None, dict(still, Layout_CloudType=(1, 1, 1, 2)))
Config tuple: (name, console_commands, view_sample_scale[, layer_height_km or None[, {param: scalar | (r, g, b, a)}
               [, {component_setter_suffix: value}]]]).
Offline (numpy, pillow; no Editor):
    python -c "import pie_cloud_flicker as f; f.report('spk', ['t50', 't20', 't50b'], out=r'<Saved>/VibeUE/CloudFlicker/')"
"""
import glob
import json
import os
import time

try:
    import unreal
except ImportError:        # offline report()
    unreal = None

if unreal:
    OUT = os.path.join(unreal.Paths.project_saved_dir(), 'VibeUE', 'CloudFlicker') + '/'
    SHOTS = os.path.join(unreal.Paths.project_saved_dir(), 'Screenshots', 'WindowsEditor')


def start(tag, configs, view, frames=8, settle=5.0, pan_dps=0.0, every_s=0.0):
    """every_s: seconds between grabs (0 = consecutive frames)."""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    assert w, 'start PIE first'
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    comp = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.VolumetricCloud)[0].get_component_by_class(unreal.VolumetricCloudComponent)
    mat = comp.get_editor_property('material')
    if not isinstance(mat, unreal.MaterialInstanceDynamic):     # never write test values into the saved instance
        mat = unreal.MaterialLibrary.create_dynamic_material_instance(w, mat)
        comp.set_material(mat)
    loc, (p, y) = view
    pc.get_controlled_pawn().set_actor_location(unreal.Vector(*loc), False, True)
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=p, yaw=y))
    st = {'k': 0, 'phase': 'set', 't': time.time(), 't0': time.time(), 'n': 0, 'last': 0.0, 'log': {}}

    def tick(dt):
        try:
            if st['k'] >= len(configs):
                open(OUT + tag + '.json', 'w').write(json.dumps(st['log']))
                unreal.unregister_slate_post_tick_callback(st['h'])
                return
            cfg = configs[st['k']]
            name, cmds, samples = cfg[:3]
            now = time.time() - st['t']
            if pan_dps and st['phase'] != 'set':
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=p, yaw=y + pan_dps * (time.time() - st['t0'])))
            if st['phase'] == 'set':
                for c in cmds:
                    unreal.SystemLibrary.execute_console_command(w, c)
                comp.set_view_sample_count_scale(samples)
                if len(cfg) > 3 and cfg[3]:
                    comp.set_layer_height(cfg[3])
                for k, v in (cfg[4] if len(cfg) > 4 else {}).items():
                    if isinstance(v, tuple):
                        mat.set_vector_parameter_value(k, unreal.LinearColor(*v))
                    else:
                        mat.set_scalar_parameter_value(k, v)
                for k, v in (cfg[5] if len(cfg) > 5 else {}).items():
                    getattr(comp, 'set_' + k)(v)
                st.update(phase='settle', t=time.time(), t0=time.time())
            elif st['phase'] == 'settle' and now > settle:
                st['log'][name] = json.loads(unreal.PerformanceService.frame_timing())
                st.update(phase='shoot', before=set(os.listdir(SHOTS)), n=0, last=0.0)
            elif st['phase'] == 'shoot' and time.time() - st['last'] >= every_s:
                unreal.SystemLibrary.execute_console_command(w, 'Shot')   # one request per frame
                st.update(n=st['n'] + 1, last=time.time())
                if st['n'] >= frames:
                    st.update(phase='collect', t=time.time())
            elif st['phase'] == 'collect' and now > 2.0:
                new = sorted(set(os.listdir(SHOTS)) - st['before'])
                for i, f in enumerate(new):
                    os.replace(os.path.join(SHOTS, f), OUT + '%s_%s_%02d.png' % (tag, name, i))
                st['log'][name]['frames'] = len(new)
                st.update(k=st['k'] + 1, phase='set', t=time.time())
        except Exception as e:
            open(OUT + tag + '.json', 'w').write(json.dumps({'error': repr(e), 'log': st['log']}))
            unreal.unregister_slate_post_tick_callback(st['h'])

    st['h'] = unreal.register_slate_post_tick_callback(tick)
    print('pie_cloud_flicker started', tag, len(configs), 'configs x', frames, 'frames ->', OUT + tag + '.json when done')


def report(tag, names, out=None, sky_rows=0.45, keep=False):
    """Per config: GPU ms, grain = mean |frame0 - blur(frame0, 2 px)| and flicker =
    mean over sky pixels of (sum |f[t+1] - f[t]| - |f[N-1] - f[0]|) / (N - 1). Deletes frames after the first
    unless keep. Whole-frame means dilute small artifacts: also compare same-region crops of frame 00 by eye."""
    import numpy as np
    from PIL import Image, ImageFilter
    out = out or OUT
    log = json.load(open(out + tag + '.json'))
    for n in names:
        files = sorted(glob.glob(out + '%s_%s_[0-9][0-9].png' % (tag, n)))
        assert len(files) >= 2, 'no burst for ' + n
        im0 = Image.open(files[0]).convert('L')
        rows = int(im0.size[1] * sky_rows)
        grain = np.abs(np.asarray(im0, np.float32) - np.asarray(im0.filter(ImageFilter.GaussianBlur(2)), np.float32))[:rows]
        f = np.stack([np.asarray(Image.open(x).convert('L'), np.float32) for x in files])[:, :rows]
        osc = (np.abs(np.diff(f, axis=0)).sum(0) - np.abs(f[-1] - f[0])) / (len(f) - 1)
        print('%-12s gpu %5.2f ms | frames %2d | grain %.2f | flicker %.3f | pixels flickering >4/frame %.2f%%' % (
            n, log[n]['gpu_ms'], len(f), grain.mean(), osc.mean(), 100 * (osc > 4).mean()))
        if not keep:
            for x in files[1:]:
                os.remove(x)
