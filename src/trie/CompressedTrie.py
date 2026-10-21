from .node import Node

class CompressedTrie:
    def __init__(self):
        self.root = Node()

    @staticmethod
    def findCommonPrefix(hash_1: str, hash_2: str) -> int:
        """Retorna o tamanho do prefixo comum entre duas strings."""
        length = 0
        while length < min(len(hash_1), len(hash_2)) and hash_1[length] == hash_2[length]:
            length += 1
        return length

    def clear(self):
        self.root = Node()

    def insert(self, hash: str, deliverer):
        current_node = self.root

        while hash:
            matched = False

            for key, child_node in list(current_node.children.items()):
                prefix_len = self.findCommonPrefix(key, hash)

                if prefix_len == 0:
                    continue

                matched = True

                # Caso A: A chave inteira do nó bate com o início do hash inserido
                if prefix_len == len(key):
                    if prefix_len == len(hash):
                        # Chave idêntica ao hash inserido
                        child_node.isEndOfHash = True
                        child_node.content.append(deliverer)
                        return
                    else:
                        # O nó atual é um prefixo do hash -> avança para o nó filho
                        hash = hash[prefix_len:]
                        current_node = child_node
                        break

                # Caso B: Prefixo parcial (a chave do nó precisa ser dividida)
                partial_prefix = key[:prefix_len]
                old_suffix = key[prefix_len:]
                new_suffix = hash[prefix_len:]

                # Criamos um novo nó intermediário
                split_node = Node()

                # Substituímos a chave antiga no nó pai pela chave do prefixo compartilhado
                del current_node.children[key]
                current_node.children[partial_prefix] = split_node

                # O nó filho antigo passa a ficar abaixo do novo nó intermediário
                split_node.children[old_suffix] = child_node

                # Tratamos o novo sufixo a ser inserido
                if new_suffix == "":
                    split_node.isEndOfHash = True
                    split_node.content.append(deliverer)
                else:
                    new_node = Node(isEndOfHash=True)
                    new_node.content.append(deliverer)
                    split_node.children[new_suffix] = new_node

                return

            # Se nenhuma chave em children coincidiu com o início do hash
            if not matched:
                new_node = Node(isEndOfHash=True)
                new_node.content.append(deliverer)
                current_node.children[hash] = new_node
                return

    def collectAllContent(self, node: Node, visited=None) -> list:
        """Reúne recursivamente os elementos armazenados a partir de um nó."""
        if visited is None:
            visited = set()

        # Proteção definitiva contra recursão infinita se houver referência circular
        if id(node) in visited:
            return []
        visited.add(id(node))

        results = []
        if node.isEndOfHash:
            results.extend(node.content)

        for child in node.children.values():
            results.extend(self.collectAllContent(child, visited))

        return results

    def searchPrefix(self, hash: str) -> list:
        """Busca e retorna os elementos cujos Geohashes começam pelo prefixo."""
        current_node = self.root

        while hash:
            matched = False

            for key, child_node in current_node.children.items():
                prefix_len = self.findCommonPrefix(key, hash)

                if prefix_len == 0:
                    continue

                matched = True

                # Caso 1: Encontrou todo o prefixo/hash buscado
                if prefix_len == len(hash):
                    return self.collectAllContent(child_node)

                # Caso 2: A chave do nó diverge do hash buscado no meio do caminho
                # Exemplo: chave do nó é "7h2abc" e a busca é "7h2xngze" (prefix_len é 3 < len(key) 6)
                if prefix_len < len(key):
                    return []

                # Caso 3: A chave do nó é um prefixo exato do hash (prefix_len == len(key))
                # Avança na árvore consumindo a parte casada do hash
                hash = hash[prefix_len:]
                current_node = child_node
                break

            if not matched:
                return []

        # Se o hash ficou vazio exatamente ao chegar em um nó
        return self.collectAllContent(current_node)
