from datetime import datetime
from Utils.auth import token_required
from flask import Blueprint, request, jsonify, Flask
from Models.cartao_model import Cartao
from flask_cors import CORS
from dateutil import parser

app = Flask(__name__)
CORS(app)
cartao_bp = Blueprint('cartao_bp', __name__)

def parse_venc_fatura(data_str):
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        try:
            dt = parser.parse(data_str)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return None

@cartao_bp.route('/cartoes', methods=['POST'])
@token_required
def criar_cartao(usuario_id):
    dados = request.json
    limite = dados.get('limite')
    venc_fatura = dados.get('venc_fatura')
    fk_id_conta = dados.get('fk_id_conta')

    if limite is None or venc_fatura is None or fk_id_conta is None:
        return jsonify({'erro': 'limite, venc_fatura e fk_id_conta são obrigatórios'}), 400

    venc_fatura_us = parse_venc_fatura(venc_fatura)
    if venc_fatura_us is None:
        return jsonify({'erro': 'Formato de data inválido para venc_fatura. Use dd/mm/yyyy ou formato válido de data'}), 400

    cartao = Cartao(limite, venc_fatura_us, fk_id_conta)

    cartao_adicionado = Cartao.adicionar(cartao)
    if cartao_adicionado is None:
        return jsonify({'erro': 'Falha ao adicionar cartão'}), 500

    # Aqui, se quiser retornar no formato BR para o cliente, pode converter novamente antes de retornar
    retorno = cartao_adicionado.to_dict()
    try:
        # converter de volta para dd/mm/yyyy para o front
        retorno['venc_fatura'] = datetime.strptime(retorno['venc_fatura'], '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        pass

    return jsonify(retorno), 201

@cartao_bp.route('/cartoes', methods=['GET'])
def listar_todos_cartoes():
    cartoes = Cartao.listar_todos()
    lista = []
    for c in cartoes:
        d = c.to_dict()
        try:
            d['venc_fatura'] = datetime.strptime(d['venc_fatura'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            pass
        lista.append(d)
    return jsonify(lista), 200


@cartao_bp.route('/cartoes/<int:id_cartao>', methods=['GET'])
def buscar_cartao(id_cartao):
    cartao = Cartao.buscar_por_id(id_cartao)
    if cartao is None:
        return jsonify({'erro': 'Cartão não encontrado'}), 404

    d = cartao.to_dict()
    try:
        d['venc_fatura'] = datetime.strptime(d['venc_fatura'], '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        pass

    return jsonify(d), 200

@cartao_bp.route('/cartoes/usuario/<int:id_usuario>', methods=['GET'])
@token_required
def listar_cartoes_usuario(usuario_id_token, id_usuario):
    # Segurança: só permite listar os próprios cartões
    if usuario_id_token != id_usuario:
        return jsonify({'erro': 'Acesso não autorizado a cartões de outro usuário'}), 403

    cartoes = Cartao.listar_por_usuario(id_usuario)
    lista = []
    for c in cartoes:
        d = c.to_dict()
        try:
            d['venc_fatura'] = datetime.strptime(d['venc_fatura'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            pass
        lista.append(d)
    return jsonify(lista), 200


@cartao_bp.route('/cartoes', methods=['PUT'])
@token_required
def atualizar_cartao(usuario_id):
    dados = request.json
    limite = dados.get('limite')
    venc_fatura = dados.get('venc_fatura')  # formato esperado dd/mm/yyyy
    fk_id_conta = dados.get('fk_id_conta')

    # fk_id_conta é obrigatório para saber qual cartão atualizar
    if fk_id_conta is None:
        return jsonify({'erro': 'fk_id_conta é obrigatório para atualizar o cartão'}), 400

    # Verificar se pelo menos um campo para atualizar foi enviado (exceto fk_id_conta)
    if limite is None and venc_fatura is None:
        return jsonify({'erro': 'Pelo menos um dos campos limite ou venc_fatura deve ser informado'}), 400

    campos_atualizar = {}

    if limite is not None:
        campos_atualizar['limite'] = limite

    if venc_fatura is not None:
        try:
            # Converte de dd/mm/yyyy para yyyy-mm-dd (formato ISO)
            venc_fatura_us = datetime.strptime(venc_fatura, '%d/%m/%Y').strftime('%Y-%m-%d')
            campos_atualizar['venc_fatura'] = venc_fatura_us
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido para venc_fatura. Use dd/mm/yyyy'}), 400

    # Busca o cartão pelo fk_id_conta
    cartao = Cartao.buscar_por_fk_id_conta(fk_id_conta)
    if cartao is None:
        return jsonify({'erro': 'Cartão não encontrado para a conta informada'}), 404

    id_cartao = cartao.id

    # Atualiza o cartão
    sucesso = Cartao.atualizar(id_cartao, campos_atualizar)
    if not sucesso:
        return jsonify({'erro': 'Falha ao atualizar cartão'}), 500

    # Busca o cartão atualizado para retornar
    cartao_atualizado = Cartao.buscar_por_id(id_cartao)
    d = cartao_atualizado.to_dict()

    # Converter venc_fatura para formato dd/mm/yyyy para o front
    try:
        d['venc_fatura'] = datetime.strptime(d['venc_fatura'], '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        pass

    return jsonify(d), 200


@cartao_bp.route('/cartoes/<int:id_cartao>', methods=['DELETE'])
@token_required
def deletar_cartao(usuario_id, id_cartao):
    # Opcional: você pode fazer uma verificação se o cartão pertence ao usuário antes de deletar, para segurança.
    # Aqui vamos só deletar diretamente.

    sucesso = Cartao.deletar_por_id(id_cartao)
    if sucesso:
        return jsonify({'mensagem': 'Cartão deletado com sucesso'}), 200
    else:
        return jsonify({'erro': 'Falha ao deletar cartão ou cartão não encontrado'}), 404
