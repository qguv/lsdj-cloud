class Models:
    def __init__(self, store):
        self.store = store

    def tracks(self):
        tracks = dict()
        for full_name, obj in self.store.items('track').items():
            # with extension
            try:
                name, version = tuple(full_name.split('.')[-3:-1])

            # without FIXME remove
            except ValueError:
                name, version = tuple(full_name.split('.')[-2:])

            version = int(version.lstrip('0'), 16)

            tracks[name] = tracks.get(name, dict(versions=dict(), size=0))
            tracks[name]['size'] += obj.size
            tracks[name]['versions'][version] = dict(size=obj.size, full_name=full_name)
        return tracks

    def srams(self):
        return self.store.items('sram')
