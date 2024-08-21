from ftplib import FTP
import pandas as pd 
import shutil
import os
import re

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
        nome_backup = '{}_{}_{}'.format(self.subestacao,self.equipamento,self.nome_grupo) + '__backup' + self.nome_extensao
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
    def atualizar_parametro(self,parametro,valor,nome_exato = True,contem_nome = False):
        with open(self.nome_arq_baixado,"r") as arquivo:
            linhas = arquivo.readlines()
            
            # Procura o parâmetro pelo nome exato
            if((contem_nome == False) and (nome_exato == True)):
                for i,linha in enumerate(linhas):
                    # Se o nome do parâmetro foi encontrado na linha...
                        if linha.startswith(parametro + ',') == True: 
                        
                            # Endereço da linha do parâmetro
                            indice = i
                            linha_p = linha
                            
                            # Delimitação de onde começa e termina a string do valor do parâmetro
                            inicio = linha_p.find("\"")+ 1
                            final = linha_p.find("\"",inicio)
                            
                            # Printa o valor do parâmetro antes da mudança
                            #print("O valor antes da atualização era {}".format(linha_p))
                            
                            #Atualiza o valor da linha do parâmetro
                            linha_p = linha_p.replace(linha[inicio:final],valor) # Corrigir isso aqui
                            
                            # Printa o valor do parâmetro depois da mudança
                            #print("O valor depois da atualização é {}".format(linha_p))
                            
                            # Colocando a linha atualizada no novo arquivo
                            linhas[i] = linha_p
                            break
            # Procura o primeiro nome que mais se aproxima do parametro procurado
            elif((contem_nome == True) and (nome_exato == False)):
                for i,linha in enumerate(linhas):
                    # Se o nome do parâmetro foi encontrado na linha...
                    if linha.find(parametro) != -1: 
                    
                        # Endereço da linha do parâmetro
                        indice = i
                        linha_p = linha
                        
                        # Delimitação de onde começa e termina a string do valor do parâmetro
                        inicio = linha_p.find("\"")+ 1
                        final = linha_p.find("\"",inicio)
                        
                        # Printa o valor do parâmetro antes da mudança
                        #print("O valor antes da atualização era {}".format(linha_p))
                        
                        #Atualiza o valor da linha do parâmetro
                        linha_p = linha_p.replace(linha[inicio:final],valor) # Corrigir isso aqui
                        
                        # Printa o valor do parâmetro depois da mudança
                        #print("O valor depois da atualização é {}".format(linha_p))
                        
                        # Colocando a linha atualizada no novo arquivo
                        linhas[i] = linha_p
                        break

        with open(self.nome_arq_baixado,"w") as arquivo:
            # Escrevendo linhas atualizadas no arquivo
            arquivo.writelines(linhas)

    def verificar_compatibilidade(self,arquivo_backup):
        # arquivo_backup - String com o nome do primeiro arquivo com .txt
        # Retorna o número de linhas diferentes entre os dois arquivos
        
        linhas_puladas1 = 0
        linhas_puladas2 = 0
    
        # Conta o número de linhas que estão no cabeçalho do arquivo para pulá-las
        with open(arquivo_backup, "r") as arquivo:
            for linha in arquivo.readlines():
                linhas_puladas1+=1
                if((linha.find("[") != -1) and (linha != "[INFO]\n")): 
                    break
        with open(self.nome_arq_baixado, "r") as arquivo:
            for linha in arquivo.readlines():
                linhas_puladas2+=1
                if((linha.find("[") != -1) and (linha != "[INFO]\n")):
                    break
        # Lê os arquivos pulando as primeiras linhas
        arq_backup = pd.read_csv(arquivo_backup,skiprows = linhas_puladas1,sep = ',')
        arq_atualizado = pd.read_csv(self.nome_arq_baixado,skiprows = linhas_puladas2,sep = ',')
        # Compara o arquivo baixado com o arquivo atualizado e retorna um DataFrame com diferenças
        comparacao_df = arq_backup.compare(arq_atualizado)
        n_linhas_alteradas = comparacao_df.shape[0]
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
    def __init__(self,ip,usuario,senha,subestacao,equipamento):
        super().__init__(ip,usuario,senha,subestacao,equipamento)
        self.ftp = FTP(ip,usuario,senha,timeout = 30)
        status = self.ftp.getwelcome()
        print(status)
        self.nome_arq_rele = None # Nome do arquivo que vai ser baixado
        
    def verificar_rid_ftp(self):
        # Baixa o arquivo do primeiro grupo do relé e verifica a identificação dele (RID)

        # host - Utiliza os últimos 3 digitos do ip para identificar o arquivo que contém o RID do relé
        host = self.ip.split(".")[3]

        
        n_grupo = 1
        try:
            
            arquivo_atualizado = "{}_{}_SET_1__atualizado.TXT".format(self.subestacao,host)
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
            

    def baixar_arquivos_ftp(self,nome_arq_rele):
        # Baixa o arquivo solicitado por conexão FTP
        # nome_arq_rele - nome do arquivo do Rele que se deseja baixar (ex SET_G.TXT)
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
            

    def enviar_arquivo_atualizado(self,arquivo_backup,arquivo_atualizado):
        # arquivo_backup - Nome de um dos backups para verificar compatibilidade (Ex : SE_RIDI_SET_X_backup 1.TXT)
        # arquivo_atualizado - Nome do arquivo que será enviado (Ex : SE_RIDI_SET_X_atualizado.TXT)
        arq = Arquivo(arquivo_atualizado,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
        diferencas = arq.verificar_compatibilidade(arquivo_backup)
        # Se a diferença entre o backup e o arquivo atualizado é menor que dois...
        if(diferencas<=2):
            with open(arquivo_atualizado, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                self.ftp.storbinary("STOR " + self.nome_arq_rele,file)

            # Baixa os arquivos após enviar as alterações para verificar se houve alterações
            arquivo_pos_alteracao = arquivo_atualizado.split("_atualizado")[0] + '__baixado' + arquivo_atualizado.split("_atualizado")[1]
            with open(arquivo_pos_alteracao,'wb') as arquivo_local: 
                self.ftp.retrbinary('RETR ' + self.nome_arq_rele,arquivo_local.write)
            arq_pos_ajuste = Arquivo(arquivo_pos_alteracao,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
            diferencas_pos_ajuste = arq_pos_ajuste.verificar_compatibilidade(arquivo_atualizado)
            if(diferencas_pos_ajuste == 0):
                print("As alterações foram enviadas com sucesso")
                return True
            else:
                print("As alterações do {} não foram enviadas".format(self.ip))
                return False
        else:
            print("Está tentando se enviar um arquivo que tem {} parâmetros diferentes do original".format(diferencas))

    
    def enviar_backup(self,arquivo_backup,nome_arq_rele):
        # arquivo_backup - Nome do arquivo de backup
        # nome_arq_rele - Nome do arquivo do relé (SET_G.TXT,SET_1.TXT, etc)

        if(nome_arq_rele in self.ftp.nlst()):

            with open(arquivo_backup, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                self.ftp.storbinary("STOR " + nome_arq_rele,file)

        # Se o nome do arquivo não está dentro dessa pasta, entre na pasta SETTINGS     
        #    
        elif('SETTINGS' in self.ftp.nlst()):
            self.ftp.cwd('SETTINGS') 
            # Abre um novo arquivo local
            with open(arquivo_backup, "rb") as file:
                # Faz o upload das alterações de arquivo_atualizado no arquivo do Rele
                self.ftp.storbinary("STOR " + nome_arq_rele,file)




        # Baixa os arquivos após enviar as alterações para verificar se houve alterações
        arquivo_pos_alteracao = arquivo_backup.split("__backup")[0] + '__baixado' + arquivo_backup.split("__backup")[1]
        with open(arquivo_pos_alteracao,'wb') as arquivo_local: 
            self.ftp.retrbinary('RETR ' + nome_arq_rele,arquivo_local.write)
        arq_pos_ajuste = Arquivo(arquivo_pos_alteracao,self.ip,self.usuario,self.senha,self.subestacao,self.equipamento)
        diferencas_pos_ajuste = arq_pos_ajuste.verificar_compatibilidade(arquivo_backup)
        if(diferencas_pos_ajuste == 0):
            print("As alterações foram enviadas com sucesso")
            return True
        else:
            print("As alterações do {} não foram enviadas".format(self.ip))
            return False

    def fechar_conexao(self):
        self.ftp.quit()
        print("Conexão FTP fechada")





#SE_RIDI_assdsd -> arquivo_baixado
#SET_G.txt -> arquivo_rele
#SET_G -> grupo_arquivo