import json

class CartItem:

    def __init__(self, item, orderedBy):
        self.item = item
        self.orderedBy = orderedBy
        self.sharedBy = []
        self.isOrdered = False

    def get_item(self):
        return self.item

    def get_orderedBy(self):
        return self.orderedBy

    def get_sharedBy(self):
        return self.sharedBy

    def get_isOrdered(self):
        return self.isOrdered

    def addUserToItem(self, name):
        if not name in self._sharedBy:
            self.sharedBy.append(name)

    def removeUserFromItem(self, name):
        if name in self._sharedBy:
            self.sharedBy.remove(name)

    def set_isOrdered_true(self):
        self.isOrdered = True

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)