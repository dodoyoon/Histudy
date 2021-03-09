서버는 우분투 18.04 환경이다.

### Step 1. 가상환경 설정

GCP, NCP 등등을 통해서 ubuntu 18.04 서버를 만든다. 

서버를 업데이트하고 파이썬과 pip를 다운받는다.

```bash
sudo apt update

sudo apt install python-pip
sudo apt install python3-pip
```

아래 명령어를 통해서 버전을 확인한다.

```bash
python3 -V
# ex) 3.6.9

# 3.6버전이 아니라면
sudo add-apt-repository ppa:deadsnakes/ppa \
&& sudo apt update 
```

밑에 있는 블로그를 참고해서 python3의 버전을 3.6로 변경하자.

[[Django] Python 3.5에서 Python 3.7로 업그레이드 하기(mod_wsgi업그레이드) (Ubuntu)](https://dodormitory.tistory.com/10)

가상환경을 만들기 위해 필요한 `virtualenvwrapper` 를 받는다.

```bash
sudo pip3 install virtualenvwrapper
```

`.bashrc` 파일을 sudo vi ~/.bashrc로 열고, 아래 내용을 파일 제일 밑에 추가한다.

```bash
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export PROJECT_HOME=$HOME/Devel
source /usr/local/bin/virtualenvwrapper.sh
```

그리고 새로운 가상환경을 만들기 전에 아래의 명령어를 실행해서 bash 파일을 실행한다.

```bash
source ~/.bashrc
```

원하는 이름으로 가상환경을 만들고 Histudy를 git clone 한다. 그리고 필요한 Python Module를 가상환경에 다운받는다. 

```bash
mkvirtualenv histudy
# histutor 파이썬 가상환경으로 activate되어있는 상태

git clone https://github.com/dodoyoon/Histudy.git

chmod -R 777 ~/Histudy

cd ~/Histudy
pip3 install -r server_requirements.txt
```

- 참고 : 가상환경 activate / deactivate 하는 법
    - activate : `source ~/.virtualenvs/histudy/bin/activate`
    - deactivate : `deactivate`

### Step 2. HisSecret 설정

HisSecret은 Django에 사용되는 비밀번호 같은 정보가 github로 노출되지 않게 비밀번호를 저장해놓은 github private repository다. 이 HisSecret은 개개인이 만들기를 권장한다. 형식은 다음과 같다. 

django secret key는 이 사이트에서 생성할 수 있다.

[Djecrety](https://djecrety.ir/)

아래는 우리가 사용한 HisSecret에 있는 secret.json 파일이다. 

```json
{
    "DJANGO_SECRET_KEY": "장고시크릿키",
    "DB_PASSWORD": "디비비번"
}
```

이제 Histudy/pystagram/settings.py에서 SECRET_BASE 부분을 아래와 같이 절대경로로 바꿔준다. 

```python
SECRET_BASE = '/home/g21300109/HisSecret'
```

이런 방식이 싫다면 서버의 Histudy/pystagram/settings.py에서 하드코딩해도 된다. 

### Step 3. Mysql 설치 및 연동

MySQL을 서버에 설치한다.

```bash
sudo apt install mysql-server
```

- 참고: MySQL 설치 후 최초 비밀번호를 요구한다면 아래와 같이 ~/Histudy/pystagram/settings.py에 저장되어 있는 DB 비밀번호와 같이 입력한다.

기본값으로 설정되어 있는 root의 비밀번호를 바꾸기 위해서 mysql을 실행시키고 아래의 명령어를 입력한다.

```bash
sudo mysql

alter user 'root'@'localhost' identified with mysql_native_password by 'password’;
```

설정한 password는 ~/Histudy/pystagram/settings.py에 있는 DB 비밀번호에 입력한다.

MySQL이 한글로 된 데이터를 저장할 수 있도록 `default character set`을 변경해야 한다

`sudo vi /etc/mysql/my.cnf` 로 파일을 열고, 파일 끝에 아래 내용을 추가한다.

```sql
[client]
default-character-set=utf8

[mysql]
default-character-set=utf8

[mysqld]
collation-server = utf8_unicode_ci
init-connect='SET NAMES utf8'
character-set-server = utf8
```

`sudo service mysql restart`로 mysql을 재시작한다.

MySQL을 다시 실행한 뒤 utf가 제대로 변경되었는지 확인한다.

```sql
mysql -u root -p

status
```


'study'라는 이름의 DB 생성한다. 꼭 character set을 변경한 후에 생성해야지 데이터베이스의 character set도 utf로 설정된다.

```sql
CREATE DATABASE study;
```

**에러 수정**

[https://dodormitory.tistory.com/8](https://dodormitory.tistory.com/8) 링크로 가서 4 - 에러 수정 부분을 참고하여 고치자

 **테이블 생성하기**

[manage.py](http://manage.py) 파일이 있는 디렉토리로 이동하고, migrate 명령어로 테이블을 생성한다.

```bash
cd ~/Histudy

python3 manage.py makemigrations

python3 manage.py migrate

# static file을 .static_root 디렉토리에 모으는 명령어
python3 manage.py collectstatic
```

mysql에서 study의 table을 보면 정상적으로 table들이 생성된 것을 볼 수 있다.

### Step 4. Apache 설치 및 연동

`deactivate` 로 가상환경에서 빠져나온다.

**apache**와 wsgi 모듈인 libapache2-mod-wsgi, 파이썬 연결 모듈 libapache2-mod-wsgi-py3를 설치한다.

```bash
sudo apt-get install apache2                  # apache2 설치
sudo apt-get install libapache2-mod-wsgi      # wsgi 모듈
sudo apt-get install libapache2-mod-wsgi-py3
```

`sudo vim /etc/apache2/sites-available/000-default.conf` 를 통해서 파일을 열고 아래처럼 설정한다.

- 설정 파일 가이드라인

```bash
<VirtualHost *:80>

ServerAdmin webmaster@localhost

DocumentRoot /var/www/html

ErrorLog ${APACHE_LOG_DIR}/error.log

CustomLog ${APACHE_LOG_DIR}/access.log combined

<Directory {wsgi.py가 있는 디렉토리 주소}>

	<Files wsgi.py>

		Require all granted

	</Files>

</Directory>

Alias {settings.py에 STATIC_URL 변수 값} {settings.py에 STATIC_ROOT 디렉토리의 절대주소}
<Directory {settings.py에 STATIC_ROOT 디렉토리의 절대주소}>
        Require all granted
</Directory>

WSGIDaemonProcess tutor python-path={manage.py가 있는 디렉토리의 절대주소} python-home={이 프로젝트를 돌릴 때에 사용하는 virtual environment의 절대주소}
WSGIProcessGroup {프로젝트이름}
WSGIScriptAlias / {wsgi.py가 있는 디렉토리의 주소/wsgi.py}

</VirtualHost>
```

히즈튜터에 맞는 설정

```bash
<VirtualHost *:80>

# The ServerName directive sets the request scheme, hostname and port that
# the server uses to identify itself. This is used when creating
# redirection URLs. In the context of virtual hosts, the ServerName
# specifies what hostname must appear in the request's Host: header to
# match this virtual host. For the default virtual host (this file) this
# value is not decisive as it is used as a last resort host regardless.
# However, you must set it for any further virtual host explicitly.
#ServerName www.example.com

ServerAdmin webmaster@localhost
DocumentRoot /var/www/html

# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
# error, crit, alert, emerg.
# It is also possible to configure the loglevel for particular
# modules, e.g.
#LogLevel info ssl:warn

ErrorLog ${APACHE_LOG_DIR}/error.log
CustomLog ${APACHE_LOG_DIR}/access.log combined

<Directory /home/g21300109/Histudy/pystagram>
	<Files wsgi.py>
		Require all granted
	</Files>
</Directory>

# Static file(js, css 등등)이 들어있는 폴더에 Apache가 접근하게 함
Alias /static /home/g21300109/Histudy/staticfiles
<Directory /home/g21300109/Histudy/staticfiles>
        Require all granted
</Directory>

WSGIDaemonProcess histudy python-path=/home/g21300109/Histudy python-home=/home/g21300109/.virtualenvs/histudy
WSGIProcessGroup histudy
WSGIScriptAlias / /home/g21300109/Histudy/pystagram/wsgi.py

</VirtualHost>
```

이후 가상환경을 다시 작동한다.

```bash
source ~/.virtualenvs/{가상환경이름}/bin/activate
```

파이썬 모듈인 `uwsgi`를 설치한다.

```bash
pip install uwsgi
```

uwsgi 가 설치되지 않는다면 아래 블로그를 참고하자

[pip3 install uwsgi 설치 에러 Failed building wheel for uwsgi](https://integer-ji.tistory.com/294)

이제 django 사용 포트를 열어야 한다.

먼저 ufw로 방화벽에서 해당 포트를 개방한다. iptables의 해당 포트를 개방한다. 마지막으로 서버를 실행시켜서 해당 포트가 열린 것을 확인한다.

```bash
sudo ufw allow 8000 

sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT

python manage.py runserver 0.0.0.0:8000 
```

Server_IP_Address:8000으로 접속하면 Histudy가 떠야 정상이다.

`sudo vi /etc/apache2/ports.conf` 로 /etc/apache2/ports.conf 파이파일을 열고, 위에서 열게된 포트를 추가한다. Listen 80밑에 Listen 8000을 추가하면 된다.

```bash
#Listen 추가포트
Listen 80
Listen 8000
```

`sudo service apache2 restart` 로 Apache를 재시작한다.

이제 `Server_Ip_Address:8000`으로 접속하면 histutor가 성공적으로 보이는 것을 볼 수 있다.

### Step 5. Google Login을 위한 Social App 등록하기

[[Django] Google 계정으로 로그인하기 (로컬 서버 + 실제 서버)](https://dodormitory.tistory.com/9)

위 블로그 포스트를 참고하면 된다. Google OAuth를 사용해서 도메인 주소를 등록하고 Django에서 Google Social Application을 활성화한다. 

### Step 6. Let's Encrypt로 https 설정하기

[Let's Encrypt를 사용하여 HTTPS 설정하기](https://dodormitory.tistory.com/11)

위 블로그 포스트를 참고하자.

https설정을 마친 후 Step4의 블로그 포스트를 참고하여 https로 시작하는 도메인도 추가해줘야 한다.

### Step 7. 현재 연도와 학기 설정하기

Histudy를 사용하기 위해선 현재 연도와 학기를 설정해주어야 한다. 이를 위해선 관리자로 로그인할 필요가 있는데,관리자를 만드는 방법은 다음과 같다.

```bash
cd ~/Histudy/ # manage.py가 있는 디렉토리로 이동
python3 manage.py createsuperuser
```

`https://{histudy ip address 또는 domain name}/admin` 으로 접속하면 관리자 페이지가 나온다. 
관리자로 로그인 후, https://www.histudy.cafe24.com/set_current (이번 년도 & 학기 지정하기)로 가서 현재 년도와 학기를 지정해준다. 

### 개발 팁
1. Super User 생성하기

장고의 관리자 계정을 생성하기 위해서는 

	1. 먼저 가상환경을 켜고: source ~/.virtualenvs/histudy/bin/activate
	2. manage.py 파일이 있는 디렉토리로 이동한다. : cd ~/Histudy
	3. Super User를 생성한다. : python3 manage.py createsuperuser

이 과정을 거치면 Super User가 생성되고 장고 관리자 페이지(주소: Histutor_domain/admin)로 접속할 수 있게 된다.

2. 더 자세한 에러메시지 보기

서버에서 문제가 생기면 Server Internal Error만 달랑 떠서 문제의 원인을 정확히 알 수 없다.
그럴 때, ~/Histudy/pystagram/settings.py 파일에서 'DEBUG' 라는 변수를 True로 변경하면 됩니다.
하지만 실제 서비스에서는 보안상의 이유로 DEBUG는 False 이어야 합니다. 
따라서 에러를 고친 다음에는 DEBUG를 False로 변경해 주시기 바랍니다.

3. Static File을 수정하거나 추가한 경우

장고에서는 Static File(css, js) 들을 한 곳에 모아두고 사용한다. 
그래서 수정되거나 추가된 Static File들은 해당 디렉토리에 추가가 되어야 한다. 
이를 추가하기 위한 과정은 다음과 같다. 

	1. 먼저 가상환경을 켜고: source ~/.virtualenvs/histudy/bin/activate
	2. manage.py 파일이 있는 디렉토리로 이동한다. : cd ~/Histudy
	3. collectstatic 명령어를 실행한다. : python3 manage.py collectstatic

그러면 'This will overwrite existing files!' 와 같은 경고문이 뜨는데 그냥 yes를 치면 된다.

4. 서버에서 자주 사용하는 명령어

```bash
# Apache 관련
1. 에러로그파일 위치: /var/log/apache2/error.log
2. 아파치 Config파일 위치: /etc/apache2/sites-available/000-default-le-ssl.conf
3. 아파치 재시작: sudo service apache2 restart

```


### Reference

[https://dodormitory.tistory.com/](https://dodormitory.tistory.com/2)

[http://wanochoi.com/?p=3575](http://wanochoi.com/?p=3575)

[https://calvinjmkim.tistory.com/23](https://calvinjmkim.tistory.com/23)
