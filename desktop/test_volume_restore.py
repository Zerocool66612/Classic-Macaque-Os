"""Volume restore is opt-in, bounded, and does not change audio without saved setting."""
from unittest.mock import patch
from volume_restore import saved_volume,restore
with patch('volume_restore.QSettings') as settings:
    settings.return_value.value.return_value=None
    assert saved_volume() is None
    with patch('volume_restore.subprocess.run') as run:
        assert not restore(tries=1)
        run.assert_not_called()
    settings.return_value.value.return_value='100'
    assert saved_volume()==100
    with patch('volume_restore.shutil.which',side_effect=lambda x:'/usr/bin/'+x if x=='wpctl' else None),patch('volume_restore.subprocess.run') as run:
        run.return_value.returncode=0
        assert restore(tries=1)
        assert run.call_args.args[0]==['wpctl','set-volume','@DEFAULT_AUDIO_SINK@','100%']
    settings.return_value.value.return_value='200'
    assert saved_volume() is None
print('PASS: saved volume restored only when valid and audio sink available')
