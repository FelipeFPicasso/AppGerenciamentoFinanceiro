from Database.conexao import conectar_financeiro

class Transacao:
    def __init__(self, descricao, valor, data, fk_id_usuario,
                 fk_id_tipo_transacao, fk_id_conta, fk_id_categoria_transacao):
        self.descricao = descricao
        self.valor = valor
        self.data = data
        self.fk_id_usuario = fk_id_usuario
        self.fk_id_tipo_transacao = fk_id_tipo_transacao
        self.fk_id_conta = fk_id_conta
        self.fk_id_categoria_transacao = fk_id_categoria_transacao

    def to_dict(self):
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'data': self.data,
            'fk_id_usuario': self.fk_id_usuario,
            'fk_id_tipo_transacao': self.fk_id_tipo_transacao,
            'fk_id_conta': self.fk_id_conta,
            'fk_id_categoria_transacao': self.fk_id_categoria_transacao
        }

    @staticmethod
    def obter_id_conta_por_nome(nome_banco):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM conta WHERE nome_banco = %s", (nome_banco,))
            resultado = cursor.fetchone()
            cursor.close()
            conn.close()
            if resultado:
                return resultado[0]
            return None
        except Exception as e:
            print(f"Erro ao buscar id da conta pelo nome: {e}")
            return None

    @staticmethod
    def obter_id_categoria_por_nome(nome_categoria):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM categoria_transacao WHERE categoria = %s", (nome_categoria,))
            resultado = cursor.fetchone()
            cursor.close()
            conn.close()
            if resultado:
                return resultado[0]
            return None
        except Exception as e:
            print(f"Erro ao buscar id da categoria pelo nome: {e}")
            return None

    @staticmethod
    def obter_id_tipo_por_nome(nome_tipo):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tipo_transacao WHERE tipo = %s", (nome_tipo,))
            resultado = cursor.fetchone()
            cursor.close()
            conn.close()
            if resultado:
                return resultado[0]
            return None
        except Exception as e:
            print(f"Erro ao buscar id do tipo pelo nome: {e}")
            return None

    @classmethod
    def adicionar(cls, transacao):
        # Antes de inserir, converte os nomes para ids
        id_conta = transacao.fk_id_conta
        id_categoria = transacao.fk_id_categoria_transacao
        id_tipo = transacao.fk_id_tipo_transacao

        # Se foram passados nomes, tenta buscar os IDs
        if isinstance(id_conta, str):
            id_conta = cls.obter_id_conta_por_nome(id_conta)
            if id_conta is None:
                print("Conta não encontrada pelo nome.")
                return None

        if isinstance(id_categoria, str):
            id_categoria = cls.obter_id_categoria_por_nome(id_categoria)
            if id_categoria is None:
                print("Categoria não encontrada pelo nome.")
                return None

        if isinstance(id_tipo, str):
            id_tipo = cls.obter_id_tipo_por_nome(id_tipo)
            if id_tipo is None:
                print("Tipo não encontrado pelo nome.")
                return None

        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transacao (descricao, valor, data, fk_id_usuario, fk_id_tipo_transacao,
                                       fk_id_conta, fk_id_categoria_transacao)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """, (
                transacao.descricao,
                transacao.valor,
                transacao.data,
                transacao.fk_id_usuario,
                id_tipo,
                id_conta,
                id_categoria
            ))
            id_inserido = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return id_inserido
        except Exception as e:
            print(
                f"Erro ao inserir transação. Descrição: {transacao.descricao}, Valor: {transacao.valor}, Erro: {str(e)}")
            return None

    @classmethod
    def listar_todas(cls):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM transacao')
            data = cursor.fetchall()

            transacoes = []
            for c in data:
                transacao = Transacao(c[1],c[2],c[3],c[4],c[5],c[6],c[7])
                transacao.id = c[0]
                transacoes.append(transacao)

            cursor.close()
            conn.close()
            return transacoes
        except Exception as e:
            print(f"Erro ao listar todas as transacoes: {e}")
            return []

    @classmethod
    def listar_por_usuario(cls, id_usuario):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()

            query = 'SELECT * FROM transacao WHERE fk_id_usuario = %s'
            cursor.execute(query, (id_usuario,))
            data = cursor.fetchall()

            transacoes = []
            for c in data:
                transacao = Transacao(c[1],c[2],c[3],c[4],c[5],c[6],c[7])
                transacao.id = c[0]
                transacoes.append(transacao)

            conn.close()
            cursor.close()
            return transacoes
        except Exception as e:
            print(f"Erro ao buscar transacao: {e}")
            return []

    @classmethod
    def buscar_por_id(cls, id_transacao):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM transacao WHERE id = %s', (id_transacao,))
            data = cursor.fetchone()

            transacao = Transacao(data[1],data[2],data[3],data[4],data[5],data[6],data[7])
            transacao.id = data[0]

            cursor.close()
            conn.close()
            return transacao
        except Exception as e:
            print(f"Erro ao buscar transacao: {e}")
            return []

    @classmethod
    def atualizar(cls, id_transacao, dados):
        try:
            campos_sql = []
            valores = []

            if 'descricao' in dados:
                campos_sql.append("descricao = %s")
                valores.append(dados['descricao'])

            if 'valor' in dados:
                campos_sql.append("valor = %s")
                valores.append(dados['valor'])

            if 'categoria' in dados:
                id_categoria = cls.obter_id_categoria_por_nome(dados['categoria'])
                if id_categoria is None:
                    print("Categoria não encontrada.")
                    return False
                campos_sql.append("fk_id_categoria_transacao = %s")
                valores.append(id_categoria)

            if 'tipo' in dados:
                id_tipo = cls.obter_id_tipo_por_nome(dados['tipo'])
                if id_tipo is None:
                    print("Tipo de transação não encontrado.")
                    return False
                campos_sql.append("fk_id_tipo_transacao = %s")
                valores.append(id_tipo)

            if not campos_sql:
                print("Nenhum campo válido para atualizar.")
                return False

            valores.append(id_transacao)

            conn = conectar_financeiro()
            cursor = conn.cursor()

            query = f"UPDATE transacao SET {', '.join(campos_sql)} WHERE id = %s"
            cursor.execute(query, valores)

            sucesso = cursor.rowcount > 0
            conn.commit()
            cursor.close()
            conn.close()

            return sucesso

        except Exception as e:
            print(f"Erro ao atualizar transação: {e}")
            return False

    @classmethod
    def deletar(cls, id_transacao):
        try:
            conn = conectar_financeiro()
            cursor = conn.cursor()

            # Deleta os relatórios vinculados primeiro
            cursor.execute("DELETE FROM relatorio_transacao WHERE fk_id_transacao = %s", (id_transacao,))

            # Depois deleta a transação
            cursor.execute("DELETE FROM transacao WHERE id = %s", (id_transacao,))
            sucesso = cursor.rowcount > 0

            conn.commit()
            cursor.close()
            conn.close()

            return sucesso
        except Exception as e:
            print(f"Erro ao deletar transação: {e}")
            return False