import json
import os.path
import io
import hashlib
import re


class Collection:
    def __init__(self, app, file_prefix, cls):
        # save options
        self.app = app
        self.cls = cls
        # compute the file name
        self.file_prefix = file_prefix
        # internal dictionary which tracks all known objects
        self._objects = {}
        # load objects
        self.load()

    def load(self):
        """ loads all known objects """
        # clear tracker
        self._objects.clear()

        # check all files in the config directory
        for filename in os.listdir(self.app.path):
            if not filename.startswith(self.file_prefix):
                continue

            path = os.path.join(self.app.path, filename)
            # open the file if it exists
            with io.open(path, mode="rt", encoding="UTF8") as fd:
                # decode object (json file)
                raw_data = json.load(fd)
                # convert raw object data
                obj = self.raw_data_to_arg_dict(raw_data)
                # create the object
                self.create(**obj)

    def save(self):
        """ saves all known objects """
        # get set of all known objects
        used_names = set()

        for key, data in self._objects.items():
            # convert data and calculate hash
            raw_data = self.obj_to_raw_data(data)
            raw_json = json.dumps(raw_data, ensure_ascii=False, indent=4, sort_keys=True)
            raw_json_hash = hashlib.sha256(raw_json.encode("UTF8")).hexdigest()[:16]

            # create readable key
            readable_key = "_".join(str(x) for x in key) if isinstance(key, tuple) else str(key)
            readable_key = readable_key.lower()
            readable_key = re.sub("[^a-zA-Z0-9]", "_", readable_key)

            filename = self.file_prefix + "__" + readable_key + "__" + raw_json_hash
            path = os.path.join(self.app.path, filename)

            used_names.add(filename)

            with io.open(path, mode="wt", encoding="UTF8") as fd:
                fd.write(raw_json)

        # delete old files
        seen_filenames = {filename for filename in os.listdir(self.app.path) if filename.startswith(self.file_prefix)}
        for filename in seen_filenames - used_names:
            os.remove(os.path.join(self.app.path, filename))

    def get_all(self):
        """ return all known objects """
        return set(self._objects.values())

    def get(self, *args, **kwargs):
        """
            get the given object, signature matches the signature of cls, however
            not all data has to specified, only the arguments are needed which are
            required to the deduce the key. if the object does not exists, an error
            is raised
        """
        # compute key
        key = self.key_from_arguments(*args, **kwargs)
        # return object
        return self._objects[key]

    def create(self, *args, **kwargs):
        """ get the given object, signature matches the signature of cls """
        # compute key
        key = self.key_from_arguments(*args, **kwargs)
        # the object may not exist yet
        assert key not in self._objects, "object with key %s already exists: %s" % (key, self._objects[key])
        # create it
        self._objects[key] = self.cls(self.app, *args, **kwargs)
        # return object
        return self._objects[key]

    # virtual methods
    def key_from_arguments(self, *args, **kwargs):
        """ get the key from the arguments """
        raise NotImplementedError

    def obj_to_raw_data(self, obj):
        """ converts an object into raw data """
        raise NotImplementedError

    def raw_data_to_arg_dict(self, raw):
        """ brings obj into a form which can be consumed by cls """
        raise NotImplementedError
