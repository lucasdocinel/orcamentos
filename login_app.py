import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# Função para ler o arquivo de usuários
def read_users(file_path):
    users = {}
    with open(file_path, 'r') as file:
        for line in file:
            user, password, role = line.strip().split(':')
            users[user] = {'password': password, 'role': role}
    return users

# Função para verificar login
def check_login(username, password, users):
    return username in users and users[username]['password'] == password

# Função para gerar o documento PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, 'Orçamento', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def generate_pdf(selected_df, total_value, value_50_discount, value_20_discount):
    pdf = PDF()
    pdf.add_page()

    pdf.ln()

    pdf.set_font('Arial', '', 10)
    for _, row in selected_df.iterrows():
        pdf.cell(100, 10, row['item'])
        pdf.cell(40, 10, f"R${row['preco']:.2f}")
        pdf.ln()

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'TOTAL: R${total_value:.2f}', 0, 1)
    pdf.cell(0, 10, f'50% off: R${value_50_discount:.2f}', 0, 1)
    pdf.cell(0, 10, f'20% off: R${value_20_discount:.2f}', 0, 1)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf

# Lê os usuários do arquivo
users = read_users('users.txt')

# Inicializa a sessão do Streamlit
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''

# Interface do usuário
st.title('Laborbraz Orçamentos')

if st.session_state.logged_in:
    st.write(f'Bem-vindo, {st.session_state.username}!')
    
    # Menu de navegação
    menu = st.selectbox('Selecione uma opção', ['Selecionar Exame', 'Visualizar Tabela Completa', 'Adicionar Exame', 'Excluir Exame', 'Logout'])

    # Carregar dados do CSV
    df = pd.read_csv('itens.csv')

    if menu == 'Selecionar Exame':
        st.write('Selecione os Exames abaixo:')

        # Selecionar Exame
        selected_items = st.multiselect('Selecione os Exames', df['item'])

        if selected_items:
            selected_df = df[df['item'].isin(selected_items)]
            total_value = selected_df['preco'].sum()
            value_50_discount = total_value * 0.5
            value_20_discount = total_value * 0.8

            st.write(f'Total  : R${total_value:.2f}')
            st.write(f'20% off: R${value_20_discount:.2f}')
            st.write(f'50% off: R${value_50_discount:.2f}')

            buf = generate_pdf(selected_df, total_value, value_50_discount, value_20_discount)
            st.download_button(
                label="Baixar documento com os resultados",
                data=buf,
                file_name="Orçamento.pdf",
                mime="application/pdf"
            )

    elif menu == 'Visualizar Tabela Completa':
        st.write('Tabela Completa de Exame')
        st.dataframe(df)

    elif menu == 'Adicionar Exame' and st.session_state.role == 'master':
        st.write('Adicionar um novo Exame')
        new_item = st.text_input('Novo Exame')
        new_price = st.number_input('Preço do Novo Exame', min_value=0.0, format="%.2f")

        if st.button('Adicionar Exame'):
            if new_item:  # Verificar se o nome do exame não está vazio
                new_row = pd.DataFrame({'item': [new_item], 'preco': [new_price]})
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv('itens.csv', index=False)
                st.success('Exame adicionado com sucesso!')
                st.experimental_rerun()
            else:
                st.error('O nome do exame não pode estar vazio!')

    elif menu == 'Excluir Exame' and st.session_state.role == 'master':
        st.write('Excluir um Exame existente')
        delete_item = st.selectbox('Selecione o Exame para Excluir', df['item'])

        if st.button('Excluir Exame'):
            if not df[df['item'] == delete_item].empty:
                df = df[df['item'] != delete_item]
                df.to_csv('itens.csv', index=False)
                st.success('Exame excluído com sucesso!')
                st.experimental_rerun()
            else:
                st.error('Selecione um exame válido!')

    elif menu == 'Logout':
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.role = ''
        st.experimental_rerun()

else:
    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')

    if st.button('Login'):
        if check_login(username, password, users):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]['role']
            st.experimental_rerun()
        else:
            st.error('Usuário ou senha incorretos')
