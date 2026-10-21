class Node:
    def __init__(self, isEndOfHash: bool = False, children= None, content = None):
        self.isEndOfHash = isEndOfHash
        self.children = children if children is not None else {}
        self.content = content if content is not None else []
    

