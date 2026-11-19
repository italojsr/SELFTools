from ftplib import FTP
import pandas as pd 
import shutil
import os
import re
from time import sleep
class Rele:
    def __init__(self,ip,usuario,senha,subestacao,equipamento):
        self.ip = ip
        self.usuario = usuario
        self.senha = senha
        self.subestacao = subestacao
        self.equipamento = equipamento
    # Instancia um objeto do tipo Arquivo
    def abrir_arquivo(self,nome_arq_baixado):
        arq = Arquivo(nome_arq_baixado,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
        return arq
    
class Arquivo(Rele):
    def __init__(self,nome_arq_baixado,ip,usuario,senha,subestacao,equipamento):
        super().__init__(ip,usuario,senha,subestacao,equipamento)
        # nome_arq_baixado - arquivo que foi baixado do Rele ("SE_RIDI_Grupo_atualizado.txt")
        # nome_grupo - SET_G, SET_1, SET_ALL, etc
        # nome_extensao - .TXT, .XLSX, etc
        # nome_arq_rele - SET_1.TXT
        self.nome_arq_baixado = nome_arq_baixado
        grupo_status_ext = nome_arq_baixado.split("_",2)[2]
        #self.equipamento = nome_arq_baixado.split("_",2)[1]
        self.nome_grupo = grupo_status_ext.split('__')[0]
        self.nome_extensao = '.' + grupo_status_ext.split('.')[1]
        self.nome_arq_rele =  self.nome_grupo + self.nome_extensao
   
    # Verifica se já existe um backup e faz backup se não existir
    def fazer_backup(self):
        # Cria o nome do arquivo txt de backup (SE_RIDI_SET_G_backup x.TXT)
        nome_backup = self.subestacao + '_' + self.equipamento + '_' + self.nome_grupo + '__backup' + self.nome_extensao
        os.makedirs("Backup", exist_ok=True)
        nome_backup = os.path.join("Backup", nome_backup)
        # Se já existe backup retorna o existente
        if(os.path.exists(nome_backup) == True):
            pass
        # Se não existe backup lê o arquivo baixado do Rele e escreve um backup com o nome_backup
        else:
            with open(self.nome_arq_baixado,"r") as arquivo_baixado:
                with open(nome_backup,"w") as arquivo_backup:
                    shutil.copyfileobj(arquivo_baixado, arquivo_backup)
        return nome_backup
    
    # Lista todas as variáveis de um parâmetro escolhido (SVs,BIs,LTs, etc)
    def listar_parametro(self,parametro):
        with open(self.nome_arq_baixado,"r") as arquivo:
            linhas = arquivo.readlines()
            lista_parametro = []

            for i,linha in enumerate(linhas):
                # Se o nome do parâmetro foi encontrado na linha...
                if linha.startswith(parametro) == True: 
                    nome_parametro = linha.split(',')[0]
                    lista_parametro.append(nome_parametro)

        return lista_parametro
    
    # Verifica o valor de um parâmetro escolhido
    def verificar_parametro(self,parametro):
        try:
            with open(self.nome_arq_baixado,"r") as arquivo:
                linhas = arquivo.readlines()

                for i,linha in enumerate(linhas):
                    # Se o nome do parâmetro foi encontrado na linha...
                    if linha.startswith(parametro) == True: 
                        # Endereço da linha do parâmetro
                        indice = i
                        linha_p = linha
                        
                        # Delimitação de onde começa e termina a string do valor do parâmetro
                        inicio = linha_p.find("\"")+ 1
                        final = linha_p.find("\n")-1

                        valor_parametro = linha_p[inicio:final]

            return valor_parametro
        except:
            return None

    def lista_outs(self):
        with open(self.nome_arq_baixado,"r") as arquivo:
                linhas = arquivo.readlines()
                lista_outs = []
                for i,linha in enumerate(linhas):
                    # Se o nome do parâmetro foi encontrado na linha...
                    if linha.startswith('OUT') == True: 
                        lista_outs.append(linha)
        return lista_outs

    def comenta_outs(self):
        lista_outs = self.lista_outs()
        for logica in lista_outs:
            # Quebra logica pela virgula e pega o nome da OUT
            OUTx = logica.split(',')[0]
            # FIltra apenas as OUTs que tem valores
            if(len(OUTx) == 6):
                valor_out = self.verificar_parametro(OUTx)
                novo_valor = '0 # ' + valor_out
                self.atualizar_parametro(OUTx,novo_valor)
            else:
                continue
            nova_lista_outs = self.lista_outs()
        return nova_lista_outs
        
    def verificar_portas(self):
        lista_portas = []
        try:
            with open(self.nome_arq_baixado,"r") as arquivo:
                linhas = arquivo.readlines()

                for i,linha in enumerate(linhas):
                    # Se o nome do parâmetro foi encontrado na linha...
                    if linha.find("PORT") != -1: 
                        # Endereço da linha do parâmetro
                        indice = i
                        linha_p = linha
                        indice = linha_p.find(",")
                        inicio_valor = linha_p.find("\"")+ 1
                        final_valor = linha_p.find("\n")-1
                        nome_parametro = linha_p[:indice]
                        valor_parametro = linha_p[inicio_valor:final_valor]

                        # Adiciona string com o valor do parametro
                        #string_parametro = """Type=TCP/IP
                        #    Remote Hostname or IP Address={}
                        #    Remote Port={}
                        #    Hosting Type=TCP/IP
                        #    Remote Emulation=False""".format(self.ip,valor_parametro)
                        #lista_portas.append([nome_parametro,string_parametro])
                        
                        lista_portas.append([nome_parametro,valor_parametro])
                        # Delimitação de onde começa e termina a string do valor do parâmetro
            df = pd.DataFrame(lista_portas,columns = ["Portas","Valor"])
            df.set_index("Portas",inplace = True)
            return df
        except:
            return None
        
    def verificar_uso_variavel(self,variavel):
        with open(self.nome_arq_baixado,"r") as arquivo:
                linhas = arquivo.readlines()
                referencias = []
                for linha in linhas:
                    par = Parametro(linha)
                    # Se o nome do parâmetro foi encontrado na linha...
                    if par.depende_variavel(variavel): 
                        referencias.append(par.get_nome_parametro())

        return referencias
    def atualizar_parametro(self,parametro,novo_valor):
    # Compilando o padrão de regex para o parâmetro seguido de uma vírgula e o valor
        padrao = re.compile(rf"^{parametro},.*$", re.MULTILINE)

        with open(self.nome_arq_baixado,"r") as arquivo:
            conteudo = arquivo.read()

        # Substituindo o valor correspondente ao parâmetro
        conteudo_modificado = re.sub(
            padrao, 
            f"""{parametro},"{novo_valor}" """, 
            conteudo
        )

        with open(self.nome_arq_baixado, 'w') as arquivo:
            arquivo.write(conteudo_modificado)

    def verificar_compatibilidade(self,arquivo_backup):
        # arquivo_backup - String com o nome do primeiro arquivo com .txt
        # Retorna o número de linhas diferentes entre os dois arquivos

        def carregar_parametros(caminho_arquivo):
            parametros = {}
            parametros_duplicados = set()

            with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
                for linha in arquivo:
                    linha = linha.strip()
                    if (not linha) or linha.startswith("[") or ("," not in linha):
                        continue

                    nome_parametro, valor_parametro = linha.split(",", 1)
                    nome_parametro = nome_parametro.strip()
                    valor_parametro = valor_parametro.strip().strip('"')

                    if nome_parametro in parametros and parametros[nome_parametro] != valor_parametro:
                        parametros_duplicados.add(nome_parametro)

                    parametros[nome_parametro] = valor_parametro

            return parametros, parametros_duplicados

        parametros_backup, duplicados_backup = carregar_parametros(arquivo_backup)
        parametros_atualizado, duplicados_atualizado = carregar_parametros(self.nome_arq_baixado)

        chaves = set(parametros_backup.keys()).union(set(parametros_atualizado.keys()))
        n_linhas_alteradas = sum(
            1 for chave in chaves if parametros_backup.get(chave) != parametros_atualizado.get(chave)
        )

        # Se houver parâmetros repetidos com valores divergentes, conta como diferença.
        n_linhas_alteradas += len(duplicados_backup.union(duplicados_atualizado))

        ##### Colocar n_linhas_alteradas no relatório
        return n_linhas_alteradas
    
class Parametro:
    def __init__(self,linha_parametro):
        # linha_parametro - String com o nome e valor do parametro, conforme cada linha do .txt
        self.__nome_parametro = linha_parametro.split(",")[0]
        inicio = linha_parametro.find("\"")+ 1
        final = linha_parametro.find("\n")-1
        self.__logica = linha_parametro[inicio:final]
    def get_nome_parametro(self):
        return self.__nome_parametro
    def get_logica(self):
        return self.__logica
    # Verifica se a lógica depende de uma variável
    def depende_variavel(self,variavel_logica):
        if(variavel_logica in self.get_logica()):
            return True
        else:
            return False

            


class ReleFTP(Rele):
    def __init__(self,ip,usuario,senhas,subestacao,equipamento):
        super().__init__(ip,usuario,senhas,subestacao,equipamento)
        self.ftp = None
        credenciais = list(senhas) if isinstance(senhas, (list, tuple, set)) else [senhas]
        self.senhas = credenciais
        self.senha = None
        for senha in credenciais:
            try:
                ftp = FTP(ip,usuario,senha,timeout=30)
                status = int(ftp.getwelcome()[:3])
                if(status!=220):
                    print(f"Falha ao conectar via FTP com senha {senha}. Status: {status}")
                    ftp.close()
                    continue
                print(status)
                self.ftp = ftp
                self.senha = senha
                break
            except Exception as e:
                print(f"Erro ao conectar via FTP com senha {senha}: {e}")
        if self.ftp is None:
            print(f"Falha ao conectar via FTP em {ip} com todas as senhas informadas.")
        self.nome_arq_rele = None  # Nome do arquivo que vai ser baixado

    def _reconectar(self):
        print(f'Conexão FTP com {self.equipamento} caiu. Tentando restaurar')
        if self.senha is None:
            print(f"Reconexão indisponível para {self.ip}: nenhuma senha foi autenticada anteriormente.")
            self.ftp = None
            return False
        try:
            # Reutiliza somente a senha já validada para este equipamento.
            ftp = FTP(self.ip,self.usuario,self.senha,timeout=30)
            status = int(ftp.getwelcome()[:3])
            if(status!=220):
                print(f"Falha ao reconectar via FTP com senha já validada. Status: {status}")
                ftp.close()
                self.ftp = None
                return False
            self.ftp = ftp
            return True
        except Exception as e:
            print(f"Falha ao reconectar via FTP: {e}")
            self.ftp = None
            return False

    def _garantir_conexao(self):
        if self.ftp is None:
            return self._reconectar()
        if self.is_connection_alive():
            return True
        return self._reconectar()

    def _storbinary_with_retry(self, comando, file_obj):
        if not self._garantir_conexao():
            return False
        try:
            self.ftp.storbinary(comando, file_obj)
            return True
        except Exception:
            if not self._reconectar():
                return False
            file_obj.seek(0)
            self.ftp.storbinary(comando, file_obj)
            return True

    def _retrbinary_with_retry(self, comando, write_callback):
        if not self._garantir_conexao():
            return False
        tentativas = 3
        ultimo_erro = None
        for tentativa in range(tentativas):
            try:
                self.ftp.retrbinary(comando, write_callback)
                return True
            except Exception as e:
                ultimo_erro = e
                sleep(5)
                if not self._reconectar():
                    continue
                try:
                    if 'SETTINGS' in self.ftp.nlst():
                        self.ftp.cwd('SETTINGS')
                except Exception:
                    pass
        print(f"Falha no download FTP ({comando}) após {tentativas} tentativas: {ultimo_erro}")
        return False

    def _normalizar_nome_grupo(self, grupo_modificado, arquivo_referencia=None):
        # Garante extensão do arquivo remoto (ex.: SET_1 -> SET_1.TXT)
        if grupo_modificado is None:
            return grupo_modificado
        if "." in grupo_modificado:
            return grupo_modificado
        if arquivo_referencia and "." in arquivo_referencia:
            extensao = os.path.splitext(arquivo_referencia)[1]
            if extensao:
                return grupo_modificado + extensao
        return grupo_modificado + ".TXT"

    def is_connection_alive(self):
        if self.ftp is None:
            return False
        try:
            # Send a "no operation" command to check the connection
            self.ftp.voidcmd("NOOP")
            return True
        except:
            return False
        
    def verificar_rid_ftp(self):
        # Baixa o arquivo do primeiro grupo do relé e verifica a identificação dele (RID)

        # host - Utiliza os últimos 3 digitos do ip para identificar o arquivo que contém o RID do relé
        host = self.ip.split(".")[3]

        
        n_grupo = 1
        try:
            
            arquivo_atualizado = "{}_{}_SET_1__atualizado.TXT".format(self.subestacao,host)
            os.makedirs("Enviado", exist_ok=True)
            arquivo_atualizado = os.path.join("Enviado", arquivo_atualizado)
            if("SET_1.TXT" in self.ftp.nlst()):
                # Escreve os dados remotos no arquivo local
                with open(arquivo_atualizado,'wb') as arquivo_local: 
                    self.ftp.retrbinary('RETR SET_1.TXT',arquivo_local.write)

            elif('SETTINGS' in self.ftp.nlst()):
                self.ftp.cwd('SETTINGS') 

            # Abre um novo arquivo local
                with open(arquivo_atualizado,'wb') as arquivo_local: 
                    # Escreve os dados remotos no arquivo local
                    self.ftp.retrbinary('RETR SET_1.TXT',arquivo_local.write) 
            else:
                print("SET_1 não foi encontrado nos diretórios baixados")

            # Abre o arquivo baixado e verifica o rid
            arq1 = self.abrir_arquivo(arquivo_atualizado)
            rid = arq1.verificar_parametro("RID")
            did = arq1.verificar_parametro("DID")
            caracteres_invalidos = r'[-(),\\/:*?"<>|]'

            if(rid == None):
                # Se rid não é encontrado e did é encontrado
                if(did != None):
                    did = re.sub(caracteres_invalidos, "_",str(did))
                    did = did.replace(" ","")
                    encontrou = True
                    rid = did
                # Se rid nem did são encontrados
                else:
                    n_grupo = n_grupo + 1
            else:
                # Se rid é encontrado
                rid = re.sub(caracteres_invalidos, "_",str(rid))
                rid = rid.replace(" ","")
                encontrou = True

        # Nada deu certo, retorna os últimos 3 dígitos do relé com ID
        except:
            rid = host
            
        return rid
            
    def verificar_modelo(self):
        arquivo_atualizado = "{}_{}_CFG__atualizado.TXT".format(self.subestacao,self.equipamento)
        os.makedirs("Enviado", exist_ok=True)
        arquivo_atualizado = os.path.join("Enviado", arquivo_atualizado)
        if("CFG.TXT" in self.ftp.nlst()):
            # Escreve os dados remotos no arquivo local
            with open(arquivo_atualizado,'wb') as arquivo_local: 
                self.ftp.retrbinary('RETR CFG.TXT',arquivo_local.write)

        elif('SETTINGS' in self.ftp.nlst()):
            self.ftp.cwd('SETTINGS') 

        # Abre um novo arquivo local
            with open(arquivo_atualizado,'wb') as arquivo_local: 
                # Escreve os dados remotos no arquivo local
                self.ftp.retrbinary('RETR CFG.TXT',arquivo_local.write) 
        else:
            print("CFG.TXT não foi encontrado nos diretórios baixados")
            return None

        # Abre o arquivo baixado e verifica o rid
        arq1 = self.abrir_arquivo(arquivo_atualizado)
        rtype = arq1.verificar_parametro("RELAYTYPE")
        rtype = rtype.split("=")[1]
        if('7' in rtype):
            return '700'
        if('3' in rtype):
            return '300'
        else:
            return 'other'
        
    def baixar_arquivos_ftp(self,nome_arq_rele):
        # Baixa o arquivo solicitado por conexão FTP
        # nome_arq_rele - nome do arquivo do Rele que se deseja baixar (ex SET_G.TXT)

        if not self._garantir_conexao():
            print(f"Não foi possível conectar ao FTP de {self.equipamento}")
            return False

        self.nome_arq_rele = nome_arq_rele
        nome_grupo = nome_arq_rele.split('.')[0]
        nome_extensao = '.' +  nome_arq_rele.split('.')[1]
        # Baixa a identificação do relé e atribui ao nome do arquivo txt
        


        # Nome do arquivo que será atualizado
        if(self.equipamento != None):
            arquivo_atualizado = self.subestacao + '_' + self.equipamento + '_' + nome_grupo + '__atualizado' + nome_extensao
        else:
        # Caso o nome do arquivo não tenha sido encontrado é atribuido os 3 últimos digitos do ip
            arquivo_atualizado = self.subestacao + '_' + self.ip.split(".")[3] + '_' + nome_grupo + '__atualizado' + nome_extensao

        os.makedirs("Enviado", exist_ok=True)
        arquivo_atualizado = os.path.join("Enviado", arquivo_atualizado)

        # Se o nome do arquivo (e.g SET_G.TXT) está dentro da pasta
        if(nome_arq_rele in self.ftp.nlst()):
            # Escreve os dados remotos no arquivo local
            with open(arquivo_atualizado,'wb') as arquivo_local: 
                self.ftp.retrbinary('RETR ' + nome_arq_rele,arquivo_local.write)

        # Se o nome do arquivo não está dentro dessa pasta, entre na pasta SETTINGS     
        #    
        elif('SETTINGS' in self.ftp.nlst()):
            self.ftp.cwd('SETTINGS') 
            # Abre um novo arquivo local
            with open(arquivo_atualizado,'wb') as arquivo_local: 
                # Escreve os dados remotos no arquivo local
                self.ftp.retrbinary('RETR ' + nome_arq_rele,arquivo_local.write) 
        else:
            print("{} não foi encontrado nos diretórios baixados".format(nome_arq_rele))
            return False

        return True
            

    def enviar_arquivo_atualizado(self,arquivo_backup,arquivo_atualizado,grupo_modificado):
        # arquivo_backup - Nome de um dos backups para verificar compatibilidade (Ex : SE_RIDI_SET_X_backup 1.TXT)
        # arquivo_atualizado - Nome do arquivo que será enviado (Ex : SE_RIDI_SET_X_atualizado.TXT)
        # grupo modificado - Nome do grupo modificado (SET_G.TXT,SET_1.TXT,etc)
        grupo_modificado = self._normalizar_nome_grupo(grupo_modificado, arquivo_atualizado)

        if not self._garantir_conexao():
            print(f"Não foi possível conectar ao FTP de {self.equipamento}")
            return False

        arq = Arquivo(arquivo_atualizado,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
        diferencas = arq.verificar_compatibilidade(arquivo_backup)
        # Se a diferença entre o backup e o arquivo atualizado é menor que dois...
        if(diferencas<=10):
            with open(arquivo_atualizado, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                if not self._storbinary_with_retry("STOR " + grupo_modificado,file):
                    return False

            
            # Verifica se após enviar novas alterações a comunicação ainda está ativa (No caso da Porta 1 a comunicação cai)
            if (self.is_connection_alive()):
                pass
            else:
                # Se a comunicação caiu, espera 10 segundos para restaurar
                sleep(10)
                if not self._reconectar():
                    return False

            # Baixa os arquivos após enviar as alterações para verificar se houve alterações
            arquivo_pos_alteracao = arquivo_atualizado.split("_atualizado")[0] + '__baixado' + arquivo_atualizado.split("_atualizado")[1]
            os.makedirs("Baixado", exist_ok=True)
            arquivo_pos_alteracao = os.path.join("Baixado", os.path.basename(arquivo_pos_alteracao))
            print('RETR ' + grupo_modificado)
            with open(arquivo_pos_alteracao,'wb') as arquivo_local: 
                if not self._retrbinary_with_retry('RETR ' + grupo_modificado,arquivo_local.write):
                    return False
            arq_pos_ajuste = Arquivo(arquivo_pos_alteracao,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
            diferencas_pos_ajuste = arq_pos_ajuste.verificar_compatibilidade(arquivo_atualizado)
            print(f"Diferenças após ajuste: {diferencas_pos_ajuste}")
            if(diferencas_pos_ajuste == 0):
                print("As alterações foram enviadas com sucesso")
                return True
            else:
                print("As alterações do {} não foram enviadas".format(self.ip))
                return False
        else:
            print("Está tentando se enviar um arquivo que tem {} parâmetros diferentes do original".format(diferencas))

    
    def enviar_backup(self,arquivo_backup,grupo_modificado):
        # arquivo_backup - Nome do arquivo de backup
        # grupo_modificado - Nome do arquivo do relé (SET_G.TXT,SET_1.TXT, etc)
        grupo_modificado = self._normalizar_nome_grupo(grupo_modificado, arquivo_backup)

        if not self._garantir_conexao():
            print(f"Não foi possível conectar ao FTP de {self.equipamento}")
            return False

        if(grupo_modificado in self.ftp.nlst()):

            with open(arquivo_backup, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                if not self._storbinary_with_retry("STOR " + grupo_modificado,file):
                    return False

        # Se o nome do arquivo não está dentro dessa pasta, entre na pasta SETTINGS     
        #    
        elif('SETTINGS' in self.ftp.nlst()):
            self.ftp.cwd('SETTINGS') 
            # Abre um novo arquivo local
            with open(arquivo_backup, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                if not self._storbinary_with_retry("STOR " + grupo_modificado,file):
                    return False


        # Verifica se após enviar novas alterações a comunicação ainda está ativa (No caso da Porta 1 a comunicação cai)
        if (self.is_connection_alive()):
            pass
        else:
            # Se a comunicação caiu, espera 10 segundos para restaurar
            sleep(10)
            if not self._reconectar():
                return False

        # Baixa os arquivos após enviar as alterações para verificar se houve alterações
        arquivo_pos_alteracao = arquivo_backup.split("__backup")[0] + '__baixado' + arquivo_backup.split("__backup")[1]
        os.makedirs("Baixado", exist_ok=True)
        arquivo_pos_alteracao = os.path.join("Baixado", os.path.basename(arquivo_pos_alteracao))
        with open(arquivo_pos_alteracao,'wb') as arquivo_local: 
            if not self._retrbinary_with_retry('RETR ' + grupo_modificado,arquivo_local.write):
                return False
        arq_pos_ajuste = Arquivo(arquivo_pos_alteracao,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
        diferencas_pos_ajuste = arq_pos_ajuste.verificar_compatibilidade(arquivo_backup)
        if(diferencas_pos_ajuste == 1):
            print("As alterações foram enviadas com sucesso")
            return True
        else:
            print("As alterações do {} não foram enviadas".format(self.ip))
            return False

    def fechar_conexao(self):
        if self.ftp is None:
            print("Sem conexão FTP ativa para fechar")
            return
        try:
            self.ftp.quit()
            print("Conexão FTP fechada")
        except Exception as e:
            print(f"Erro ao fechar conexão FTP: {e}")





#SE_RIDI_assdsd -> arquivo_baixado
#SET_G.txt -> arquivo_rele
#SET_G -> grupo_arquivo