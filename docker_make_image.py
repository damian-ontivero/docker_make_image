#!/usr/bin/python3

# Damián Ontivero - Python script to make Docker images
import sys
import os
import subprocess
import requests
import tarfile
import datetime


class DockerImage:

    def __init__(self, username, password, url, docker_image_tag):
        # Necessary parameters to invoque the script
        self.username = username
        self.password = password
        self.url = url
        self.docker_image_tag = docker_image_tag
        # Necessary variables
        self.project_file = os.path.basename(url)
        self.project_folder = self.project_file[:-7]


    def download_files(self):
        try:
            # Project download
            r = requests.get(self.url, auth=(self.username, self.password))
            if r.status_code == 200:
                with open(self.project_file, 'wb') as out:
                    for bits in r.iter_content():
                        out.write(bits)
            # Project extraction 
            tar = tarfile.open(self.project_file, 'r:gz')
            tar.extractall()
            tar.close()
        except:
            print('Something went wrong downloading or decompressing the files.')
        else:
            return True


    def env_var(self):
        try:
            subprocess.run(['sed', '-i', '/\/\/\'hostname\'/d', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/\/\/\'dbdriver\'/d', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/\'hostname\' =>/c\\\t\'hostname\' => \'\',', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/\'username\' =>/c\\\t\'username\' => \'\',', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/\'password\' =>/c\\\t\'password\' => \'\',', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/\'database\' =>/c\\\t\'database\' => \'\',', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '0,/\'hostname\' => \'\'/s//\'hostname\' => DB_HOST:DB_PORT/', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '0,/\'username\' => \'\'/s//\'username\' => DB_USER/', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '0,/\'password\' => \'\'/s//\'password\' => DB_PASS/', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '0,/\'database\' => \'\'/s//\'database\' => DB_NAME/', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', ':a;N;$!ba; s/\'database\' => \'\'/\'database\' => APPPATH.\'libraries\/pinesRDC.db\'/4', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/define(\'PRODUCCION\', 0 );/c\\\tdefine(\'PRODUCCION\', IS_PRODUCTION );', f'{self.project_folder}/application/config/database.php'], check = True)
            subprocess.run(['sed', '-i', '/$serverName = /c\\\t\\\t\\\t\\\t\$serverName = "DB_HOST:DB_PORT";', f'{self.project_folder}/WebServices/wssoap.php'], check = True)
            subprocess.run(['sed', '-i', '/$user.*= \'.*\'/c\\\t\\\t\\\t\\\t\$user           = \'DB_USER\';', f'{self.project_folder}/WebServices/wssoap.php'], check = True)
            subprocess.run(['sed', '-i', '/$pass.*= \'.*\'/c\\\t\\\t\\\t\\\t\$pass           = \'DB_PASS\';', f'{self.project_folder}/WebServices/wssoap.php'], check = True)
            subprocess.run(['sed', '-i', '/$BD.*= \'.*\'/c\\\t\\\t\\\t\\\t\$BD             = \'DB_NAME\';', f'{self.project_folder}/WebServices/wssoap.php'], check = True)
            subprocess.run(['sed', '-i', '/$server = new SoapServer/c\$server = new SoapServer( null, array(\'uri\' => WEB_SERVICE ));', f'{self.project_folder}/WebServices/wssoap.php'], check = True)
            subprocess.run(['sed', '-i', '/<soap:address location=/c\        <soap:address location=WEB_SERVICE_SOAP/>', f'{self.project_folder}/WebServices/webServices.wsdl'], check = True)
            subprocess.run(['sed', '-i', '/} | telnet/c\} | telnet UPDATER_HOST UPDATER_PORT', f'{self.project_folder}/application/libraries/refresca_updater.sh'], check = True)
            subprocess.run(['sed', '-i', '/$level.*= Logger::DEBUG;/c\\\t\\\t\$level                  = Logger::LOG_LEVEL;', f'{self.project_folder}/system/libraries/LogMicropago.php'], check = True)
        except:
            print('Something went wrong configuring the environment variables.')
        else:
            return True


    def make_dockerfile(self):
        # Necessary variables
        dockerfile_old = f'Dockerfile_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
        search = '# Copy web project files.'
        try:
            os.rename('Dockerfile', dockerfile_old)
            dockerfile_new = open('Dockerfile', 'w')
            flag = 0
            with open(dockerfile_old, 'r') as f:
                for line in f:
                    if flag == 1:
                        mod_line = f'COPY {self.project_folder}/ /var/www/web-rdc/\n'
                        dockerfile_new.write(mod_line)
                        flag = 0
                        continue
                    dockerfile_new.write(line)
                    if (search in line):
                        flag = 1
            dockerfile_new.close()
        except:
            print('Something went wrong making the Dockerfile.')
        else:
            return True


    def build_image(self):
        try:
            subprocess.run(['docker', 'build', '-t', f'{self.docker_image_tag}', '.'], check = True)
        except:
            print('Something went wrong building the image.')
        else:
            return True


    def push_image(self):
        try:
            subprocess.run(['docker', 'push', f'{self.docker_image_tag}'], check = True)
        except:
            print('Something went wrong uploading the image.')
        else:
            return True

try:
    docker_image = DockerImage(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
except IndexError:
    print("""The following parameters must be indicated:
            - Username
            - Password
            - Link
            - Docker image tag""")
else:
    if docker_image.download_files():
        print('Download and decompression files successful.')
        if docker_image.env_var():
            print('Environment variables configuration successful.')
            if docker_image.make_dockerfile():
                print('Dockerfile creation successful.')
                if docker_image.build_image():
                    print('Docker image build successful.')
                    if docker_image.push_image():
                        print('Docker image push successful.')
