import json

class CartItem:

    def __init__(self, item, orderedBy):
        self._item = item
        self._orderedBy = orderedBy
        self._sharedBy = []
        self._isOrdered = False

    def get_item(self):
        return self._item

    def get_orderedBy(self):
        return self._orderedBy

    def get_sharedBy(self):
        return self._sharedBy

    def get_isOrdered(self):
        return self._isOrdered

    def addUserToItem(self, name):
        if not name in self._sharedBy:
            self._sharedBy.append(name)

    def removeUserFromItem(self, name):
        if name in self._sharedBy:
            self._sharedBy.remove(name)

    def set_isOrdered_true(self):
        self._isOrdered = True

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)