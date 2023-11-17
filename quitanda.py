import os
from flask import Flask, render_template, request, redirect, session
import sqlite3 as sql
import uuid


app = Flask(__name__)
app.secret_key ="quitandazezinho"

usuario="usuario"
senha="senha"
login= False

#ROTA DA PÁGINA LOGIN
@app.route("/login")
def login():

    title="Login"
    return render_template("login.html",title=title)


#VERIFICA A SESSÃO
def verifica_sessao():
    if "login" in session and session["login"]:
        return True
    else:
        return False

#CONEXAO COM O BANCO DE DADOS
def conecta_database():
    conexao = sql.connect("db_quitanda.db")
    conexao.row_factory = sql.Row
    return conexao

#INICIAR BANCO DE DADOS
def iniciar_db():
    conexao = conecta_database()
    with app.open_resource('esquema.sql', mode='r') as comandos:
        conexao.cursor().executescript(comandos.read())
    conexao.commit()
    conexao.close()

#ROTA DA PÁGINA INICIAL
@app.route('/')
def index():
    iniciar_db() #chamando o BD
    conexao = conecta_database()
    produtos = conexao.execute('SELECT * FROM produtos ORDER BY id_prod DESC').fetchall()#colocar na ordem os post (o último por primeiro)
    conexao.close()   
    title= "Home"
    return render_template("home.html", produtos=produtos, title=title)

# ROTA DA PÁGINA ACESSO
@app.route("/acesso", methods=['post'])
def acesso():
    global usuario, senha
    usuario_informado = request.form["usuario"]
    senha_informada = request.form["senha"]
    if usuario == usuario_informado and senha == senha_informada:
        session["login"] = True
        return redirect('/adm')

    else:

        return render_template("login.html",msg="Usuário/Senha estão incorretos!")
#ROTA DO ADM
@app.route("/adm")
def adm():
    if verifica_sessao():
        iniciar_db()
        conexao = conecta_database()
        produtos = conexao.execute('SELECT * FROM produtos ORDER BY id_prod DESC').fetchall()
        conexao.close()
        title = "Administração"
        return render_template("adm.html", produtos=produtos, title=title)
    else:
        return redirect("/login")
#ROTA LOGOUT
@app.route("/logout")
def logout():
    global login
    login = False
    session.clear()
    return redirect('/')

#ROTA  DA PÁGINA DE CADASTRO
@app.route("/cadprodutos")
def cadprodutos():
    if verifica_sessao():
        iniciar_db()
        title = "Cadastro de produtos"
        return render_template("cadprodutos.html", title=title)
    else:
        return redirect('/login')

# ROTA DA PÁGINA DE CADASTRO NO BANCO 
@app.route("/cadastro", methods=["POST"])
def cadastro():
    if verifica_sessao():
        nome_prod = request.form['nome_prod']
        desc_prod = request.form['desc_prod']
        preco_prod = request.form['preco_prod']
        img_prod = request.files.get('img_prod')  # Use get para evitar erros se a chave 'img_prod' não estiver presente

        if img_prod:  # Se foi enviada uma imagem
            id_foto = str(uuid.uuid4().hex)
            filename = (id_foto + nome_prod + '.png')
            img_prod.save(os.path.join("static/img/produtos/", filename))
        else:  # Caso contrário, use uma imagem padrão
            filename = 'imagem_padrao.png'  # Substitua 'imagem_padrao.png' pelo nome do seu arquivo de imagem padrão

        conexao = conecta_database()
        conexao.execute('INSERT INTO produtos (nome_prod, desc_prod, preco_prod, img_prod) VALUES (?, ?, ?, ?)',
                        (nome_prod, desc_prod, preco_prod, filename))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")
#ROTA DE EXCLUSÃO
@app.route("/excluir/<id_prod>")
def excluir(id_prod):
    conexao = conecta_database()
    conexao.execute("DELETE FROM produtos WHERE id_prod = ?",(id_prod,))
    conexao.commit()
    conexao.close()
    return redirect('/adm')

#CRIAR A ROTA DO EDITAR
@app.route("/editprodutos/<id_prod>")
def editar(id_prod):  
    if verifica_sessao():
        iniciar_db()
        conexao = conecta_database()
        produtos =conexao.execute('SELECT * FROM produtos WHERE id_prod = ?',(id_prod,)).fetchall()
        conexao.close()
        title = "Edição de produtos"
        return render_template("editprodutos.html", produtos=produtos, title=title)
    else:
        return redirect("/login")
    



#CRIAR A ROTA PARA TRATAR A EDIÇÃO
@app.route("/editarprodutos", methods=['POST'])
def editprod():
    id_prod = request.form['id_prod']
    nome_prod=request.form['nome_prod']
    desc_prod=request.form['desc_prod']
    preco_prod=request.form['preco_prod']
    img_prod=request.files ['img_prod']

    conexao = conecta_database()
    # Obtenha a imagem atual do produto no banco de dados
    cursor = conexao.execute('SELECT img_prod FROM produtos WHERE id_prod = ?', (id_prod,))
    produto = cursor.fetchone()
    imagem_anterior = produto['img_prod'] if produto else None
    if img_prod:
        id_foto=str(uuid.uuid4().hex)
        filename=id_foto+nome_prod+'.png'
        img_prod.save(os.path.join("static/img/produtos/", filename))
        conexao = conecta_database()
        conexao.execute('UPDATE produtos SET nome_prod = ?, desc_prod = ?, preco_prod = ?, img_prod = ?  WHERE id_prod = ?', (nome_prod, desc_prod, preco_prod, filename, id_prod))
    else: # Se nenhuma nova imagem foi enviada, mantenha a imagem existente
        conexao.execute('UPDATE produtos SET nome_prod = ?, desc_prod = ?, preco_prod = ? WHERE id_prod = ?',
                        (nome_prod, desc_prod, preco_prod, id_prod))

    conexao.commit()
    conexao.close()    
        
    # Se uma nova imagem foi enviada, remova a imagem anterior (se existir)
    if img_prod and imagem_anterior:
        path_imagem_anterior = os.path.join("static/img/produtos/", imagem_anterior)
        if os.path.exists(path_imagem_anterior):
            os.remove(path_imagem_anterior)

    return redirect('/adm')

# ROTA DA PÁGINA DE BUSCA
@app.route("/busca", methods=["post"])
def busca():
    busca=request.form['buscar']
    conexao = conecta_database()
    produtos = conexao.execute('SELECT * FROM produtos WHERE nome_prod LIKE "%" || ? ||  "%" ', (busca,)).fetchall() 
    title="Home"
    return render_template("home.html", produtos=produtos, title=title)


#FINAL DO CÓDIGO - EXECUTANDO SERVIDOR
app.run(debug=True)

