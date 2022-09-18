from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
import pydantic
from functools import reduce

#db_usuarios={}
#db_produtos={}
#db_end={}
#db_carrinhos={}

app = FastAPI()

OK = "OK"
FALHA = "FALHA"


# Classe representando os dados do endereço do cliente
class Endereco(BaseModel):
    rua: str
    cep: str
    cidade: str
    estado: str


# Classe representando os dados do cliente
class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    senha: str


# Classe representando a lista de endereços de um cliente
class ListaDeEnderecosDoUsuario(BaseModel):
    usuario: Usuario
    enderecos: List[Endereco] = []


# Classe representando os dados do produto
class Produto(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float


# Classe representando o carrinho de compras de um cliente com uma lista de produtos
class CarrinhoDeCompras(BaseModel):
    id_usuario: int
    id_produtos: List[Produto] = []
    preco_total: float
    quantidade_de_produtos: int


db_usuarios = {}
db_produtos = {}
db_end = {}        # enderecos_dos_usuarios
db_carrinhos = {}


# Criar um usuário,
# se tiver outro usuário com o mesmo ID retornar falha, 
# se o email não tiver o @ retornar falha, 
# senha tem que ser maior ou igual a 3 caracteres, 
# senão retornar OK
@app.post("/usuario/")
def criar_usuário(usuario: Usuario):
    if usuario.id in db_usuarios:
        return FALHA
    elif not "@" in usuario.email:
        return FALHA
    elif len(usuario.senha)<3:
        return FALHA
    db_usuarios[usuario.id] = usuario
    return OK


# Se o id do usuário existir, retornar os dados do usuário
# senão retornar falha
@app.get("/usuario/{id}")
async def retornar_usuario(id: int):
    if id in db_usuarios:
        return db_usuarios[id]
    return FALHA


# Se existir um usuário com exatamente o mesmo nome, retornar os dados do usuário
# senão retornar falha
@app.get("/usuario/{nome}")
async def retornar_usuario_com_nome(nome: str):
    if nome in db_usuarios:
        return db_usuarios[nome]
    else:
        return FALHA


# Se o id do usuário existir, deletar o usuário e retornar OK
# senão retornar falha
# ao deletar o usuário, deletar também endereços e carrinhos vinculados a ele
@app.delete("/usuario/{id}")
async def deletar_usuario(id: int):
    if id in db_usuarios:
        del db_usuarios[id]
    else:
        return FALHA


# Se não existir usuário com o id_usuario retornar falha, 
# senão retornar uma lista de todos os endereços vinculados ao usuário
# caso o usuário não possua nenhum endereço vinculado a ele, retornar 
# uma lista vazia
### Estudar sobre Path Params (https://fastapi.tiangolo.com/tutorial/path-params/)
  
@app.get("/usuario/{id_usuario}/endereços/")
async def retornar_enderecos_do_usuario(id_usuario: int):
    if id not in db_end:
        return []
    else:
        return db_end[id]
    
@app.delete ("usuario/endereço/{id}")
async def deletar_endereço(id:int):
    if id not in db_end:
        return FALHA
    else: 
        del db_end[id]
                           

# Retornar todos os emails que possuem o mesmo domínio
# (domínio do email é tudo que vêm depois do @)
# senão retornar falha
@app.get("/usuarios/emails/{dominio}")
async def retornar_emails(dominio: str):
    emails={}
    for usuario in db_usuarios.values():
        emails={}
    if usuario.email.split("@")[1]==dominio:
        emails[usuario.id]=usuario.email
    if len(emails)>0:
        return emails
    else:          
        return FALHA


# Se não existir usuário com o id_usuario retornar falha, 
# senão cria um endereço, vincula ao usuário e retornar OK
@app.post("/endereco/{id_usuario}/endereço")
async def criar_endereco(id_usuario: int, endereco: Endereco):
    if id_usuario not in db_usuarios:
        return FALHA
    if id_usuario not in db_end:
        lista_end='Endereços_Usuário'()
        lista_end.usuario=db_usuarios[id_usuario]
        return OK
        

# Se não existir endereço com o id_endereco retornar falha, 
# senão deleta endereço correspondente ao id_endereco e retornar OK
# (lembrar de desvincular o endereço ao usuário)
@app.delete("/usuario/{id_usuario}/endereço{id_endereço}")
async def deletar_endereco(id_usuario:int,id_endereço:int):
    if id_usuario not in db_usuarios:
        return FALHA
    if id_usuario not in db_end:
        return FALHA
    else:
        if db_end[id_usuario].endereços[id_endereço]:
            db_end[id_usuario].endereços.pop(id_endereço)
            return OK
          

# Se tiver outro produto com o mesmo ID retornar falha, 
# senão cria um produto e retornar OK
@app.post("/produto/{id_produto}")
async def criar_produto(produto: Produto):
    if produto.id in db_produtos:
        return FALHA
    db_produtos[produto.id]=produto
    return OK


# Se não existir produto com o id_produto retornar falha, 
# senão deleta produto correspondente ao id_produto e retornar OK
# (lembrar de desvincular o produto dos carrinhos do usuário)
@app.delete("/produto/{id_produto}/")
async def deletar_produto(id_produto: int):
    if id_produto not in db_produtos:
        return FALHA
    for carrinho in db_carrinhos.values():
        for i in range(0,carrinho.produtos.count(db_produtos[id_produto])):
            carrinho.remove_produto(id_produto)
    db_produtos.pop(id_produto)
    return OK


# Se não existir usuário com o id_usuario ou id_produto retornar falha, 
# se não existir um carrinho vinculado ao usuário, crie o carrinho
# e retornar OK
# senão adiciona produto ao carrinho e retornar OK
@app.post("/carrinho/{id_usuario}/{id_produto}/")
async def adicionar_carrinho(id_usuario: int, id_produto: int):
    if id_usuario not in db_usuarios or id_produto not in db_produtos:
        return FALHA
    if id_usuario not in db_carrinhos:
        carrinho=CarrinhoDeCompras
        carrinho.id_usuario=id_usuario
        db_carrinhos[id_usuario]=carrinho
    db_carrinhos[id_usuario].adiciona_produto(db_produtos[id_produto])
    return OK


# Se não existir carrinho com o id_usuario retornar falha, 
# senão retorna o carrinho de compras.
@app.get("/carrinho/{id_usuario}/")
async def retornar_carrinho(id_usuario: int):
    if id_usuario not in db_carrinhos:
        return FALHA
    if id_usuario in db_carrinhos:
        return CarrinhoDeCompras


# Se não existir carrinho com o id_usuario retornar falha, 
# senão retorna o o número de itens e o valor total do carrinho de compras.
@app.get("/carrinho/{id_usuario}/total")
async def retornar_total_carrinho(id_usuario: int):
    if id_usuario not in  db_carrinhos:
        return FALHA
    numero_itens=db_carrinhos[id_usuario].quantidade_de_produtos 
    valor_total=db_carrinhos[id_usuario].preço_total
    return numero_itens, valor_total


# Se não existir usuário com o id_usuario retornar falha, 
# senão deleta o carrinho correspondente ao id_usuario e retornar OK
@app.delete("/carrinho/{id_usuario}/")
async def deletar_carrinho(id_usuario: int):
    if id_usuario not in db_usuarios:
        return FALHA
    db_carrinhos.pop(id_usuario)
    return OK

@app.get("/")
async def bem_vinda():
    site = "Que os jogos comecem"
    return site.replace('\n', '')
























