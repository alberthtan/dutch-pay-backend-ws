import json

class CartItem:

    def __init__(self, id, item, orderedBy, table_id):
        self.id = id
        self.item = item
        self.orderedBy = orderedBy
        self.sharedBy = []
        self.status = "pending"
        self.table_id = table_id
        self.order_id = None

    def get_id(self):
        return self.id

    def get_item(self):
        return self.item

    def get_orderedBy(self):
        return self.orderedBy

    def get_sharedBy(self):
        return self.sharedBy

    def get_status(self):
        return self.status

    def addUserToItem(self, name):
        if not name in self.sharedBy:
            self.sharedBy.append(name)

    def removeUserFromItem(self, name):
        if name in self.sharedBy:
            self.sharedBy.remove(name)

    def set_status(self, status):
        self.status = status

    def set_order_id(self, id):
        self.order_id = id

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)