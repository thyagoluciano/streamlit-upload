import streamlit as st
import os
import hashlib
from datetime import datetime
import pandas as pd
import base64

# Configuração da página
st.set_page_config(page_title="Sistema de Upload", layout="centered")

# Dicionário com usuários e senhas (em produção, use um banco de dados)
# As senhas estão com hash SHA-256
USERS = {
    'admin': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'  # senha: 123
}


def make_hash(password):
    """Cria um hash SHA-256 da senha"""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password():
    """Retorna True se as credenciais estão corretas"""
    if 'login_status' not in st.session_state:
        st.session_state['login_status'] = False

    if st.session_state['login_status']:
        return True

    # Criar formulário de login
    login_form = st.form('login')
    username = login_form.text_input('Usuário').lower()
    password = login_form.text_input('Senha', type='password')

    if login_form.form_submit_button('Login'):
        if username in USERS and USERS[username] == make_hash(password):
            st.session_state['login_status'] = True
            st.session_state['username'] = username
            return True
        else:
            st.error('Usuário ou senha incorretos')
            return False
    return False


def save_uploaded_file(uploaded_file):
    """Salva o arquivo enviado em uma pasta 'uploads'"""
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join('uploads', file_name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def get_file_size(file_path):
    """Retorna o tamanho do arquivo em formato legível"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def get_file_info():
    """Retorna informações sobre os arquivos na pasta uploads"""
    if not os.path.exists('uploads'):
        return pd.DataFrame()

    files = []
    for filename in os.listdir('uploads'):
        file_path = os.path.join('uploads', filename)
        original_name = '_'.join(filename.split('_')[2:]) if len(filename.split('_')) > 2 else filename
        upload_date = datetime.strptime('_'.join(filename.split('_')[:2]), "%Y%m%d_%H%M%S")

        files.append({
            'Nome Original': original_name,
            'Data Upload': upload_date.strftime("%d/%m/%Y %H:%M:%S"),
            'Tamanho': get_file_size(file_path),
            'Nome Arquivo': filename
        })

    return pd.DataFrame(files)


def get_download_link(filename):
    """Gera um link de download para o arquivo"""
    file_path = os.path.join('uploads', filename)
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download</a>'
    return href


def delete_file(filename):
    """Deleta um arquivo da pasta uploads"""
    file_path = os.path.join('uploads', filename)
    try:
        os.remove(file_path)
        return True
    except:
        return False


def main():
    st.title("Sistema de Upload de Arquivos")

    if check_password():
        st.success(f'Bem-vindo, {st.session_state["username"]}!')

        # Botão de logout
        if st.button('Logout'):
            st.session_state['login_status'] = False
            st.experimental_rerun()

        st.markdown("---")

        # Área de upload
        st.subheader("Upload de Arquivos")
        uploaded_file = st.file_uploader("Escolha um arquivo", type=['pdf', 'txt', 'csv', 'xlsx', 'docx'])

        if uploaded_file is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.info(f"Nome do arquivo: {uploaded_file.name}")
                st.info(f"Tipo do arquivo: {uploaded_file.type}")
                st.info(f"Tamanho: {uploaded_file.size} bytes")

            with col2:
                if st.button("Salvar Arquivo"):
                    file_path = save_uploaded_file(uploaded_file)
                    st.success(f"Arquivo salvo com sucesso!")

        # Tabela de arquivos
        st.markdown("---")
        st.subheader("Arquivos Disponíveis")

        df = get_file_info()
        if not df.empty:
            # Criar colunas para ações (download e delete)
            df['Ações'] = df['Nome Arquivo'].apply(lambda x: f'{get_download_link(x)} | ')

            # Mostrar tabela sem a coluna de nome do arquivo (que é usado internamente)
            st.write(df.drop('Nome Arquivo', axis=1).to_html(escape=False, index=False), unsafe_allow_html=True)

            # Área para deletar arquivos
            st.markdown("---")
            st.subheader("Excluir Arquivos")

            col1, col2 = st.columns([3, 1])
            with col1:
                file_to_delete = st.selectbox("Selecione o arquivo para excluir",
                                              df['Nome Original'].tolist(),
                                              index=None,
                                              placeholder="Escolha um arquivo...")

            with col2:
                if file_to_delete:
                    filename = df[df['Nome Original'] == file_to_delete]['Nome Arquivo'].iloc[0]
                    if st.button("Excluir", type="primary"):
                        if delete_file(filename):
                            st.success(f"Arquivo {file_to_delete} excluído com sucesso!")
                            st.experimental_rerun()
                        else:
                            st.error("Erro ao excluir arquivo!")
        else:
            st.info("Nenhum arquivo enviado ainda.")


if __name__ == '__main__':
    main()