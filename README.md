# Django CRUD app on Docker

Django + Nginx + Gunicorn + Dockerのリポジトリです。以下のソースを参考に、Django 3.2に対応。またdocker-composeでフレキシブルな構成にしています。

- 『現場で使えるDjangoの教科書《基礎編》』
- 『現場で使えるDjangoの教科書《実践編》』
- <a href="https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/" target="_blank">Dockerizing Django with Postgres, Gunicorn, and Nginx</a>


### 「現場で使えるDjangoの教科書《基礎編》」のベストプラクティス一覧

🎉ベストプラクティス10個

1. 分かりやすいプロジェクト構成
2. アプリケーションごとにurls.pyを配置する
3. Userモデルを拡張する
4. 発行されるクエリを確認する
5. select_related / prefetch_relatedでクエリ本数を減らす
6. ベーステンプレートを用意する
7. こんなときはModelFormを継承しよう
8. メッセージフレームワークを使う
9. 個人の開発環境の設定はlocal_settings.pyに書く
10. シークレットな変数は.envファイルに書く

#### 番外 便利なDjangoパッケージを使おう(django-debug-toolbar)

```bash
pipenv install django-debug-toolbar
```

```python[config/settings.py]
if DEBUG:
  def show_toolbar(request):
    return True

  INSTALLED_APPS += (
    'django_toolbar',
  )
  MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
  )
  DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
  }
```

```python[config/urls.py]
if settings.DEBUG:
  import debug_toolbar

  urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
```


#### BP1 分かりやすいプロジェクト構成

・問題点
- ベースディレクトリと設定ディレクトリ名が同じでややこしい。
- テンプレートと静的ファイルがアプリケーションごとにバラバラに配置されてしまう。

・ベストプラクティス
- startprojectで生成されるディレクトリ名を変更する。「config」「default」「root」など。
- 本番環境ではcollectstaticコマンドでstaticfilesディレクトリにまとめる。開発環境(runserver)は自動で配信してくれる。

```bash[bash]
mkdir mysite && cd mysite
django-admin startproject config .

tree
mysite
 |-- manage.py
 `-- config
    |-- __init__.py
```

```python[config/settings.py]
STATIC_URL = '/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/mediafiles/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')
```


#### BP2 アプリケーションごとにurls.pyを配置する

startproject実行時に生成されるurls.pyのみにURLパターンの設定を追加していくと、設定がどんどん肥大化して管理が大変になる。urls.pyを分割し、アプリケーションディレクトリごとに1つずつurls.pyを配置する。

```python[config/urls.py]
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
  path('admin/', admin.site.urls),
  path('item/', include('item.urls)),
]
```

include関数を使ってアプリケーションごとのurls.pyを読み込む。「/item/」で始まるURLパターンのすべてを「item」アプリケーションのitem/urls.pyに任せる。各アプリケーションのurls.pyでは、アプリケーション内部のURLパターンの設定のみに集中できる。

```python[item/urls.py]
from django.urls import path

from . import views

app_name = 'item'
urlpatterns = [
  path('', views.itemList, name='item.list'),
  path('/<int:pk>', views.itemShow, name='item.show'),
]
```

・注意点
- startappコマンドではアプリケーションディレクトリ内にurls.pyは生成されない。自分で作成する。
- app_name(名前空間)を設定する。


#### BP3 Userモデルを拡張する

デフォルトで提供されるUserモデルには以下のフィールドがある。

<a href="https://docs.djangoproject.com/en/3.2/ref/contrib/auth/" target="_blank">django.contrib.auth</a>

class models.User

|field|
|---|
|username|
|first_name|
|last_name|
|email|
|password|
|groups|
|user_permissions|
|is_staff|
|is_active|
|is_superuser|
|last_login|
|date_joined|


デフォルトのフィールド以外にも必要なフィールドがある場合は、拡張する必要がある。拡張する方法はおもに以下の3つ。

1. 抽象クラスAbstractBaseUserを継承する -> リリース前でガラッと変えたいとき
2. 抽象クラスAbstractUserを継承する -> リリース前でチョロっと追加したいとき
3. 別モデルを作ってOneToOneFieldで関連させる -> リリースしたあと

ex: AbstractUserを継承する場合

1. Edit accounts/models.py
2. Edit config/settings.py

```python[accounts/models.py]
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
  class Meta:
    db_table = 'custom_user'

  login_count = models.IntegerField(varbose_name='ログイン回数', default=0)
```

```python[settings.py]
AUTH_USER_MODEL = 'accounts.CustomUser' # <アプリケーション名>.<モデルクラス名>
```


#### BP4 発行されるクエリを確認する

オブジェクトの検索が実行されるときにどのようなクエリが発行されるか　ーモデルの使い方は合っているか？パフォーマンスに影響はないか？ー　を確認する。

1. Djangoシェルを使う
2. ロギングの設定を変更する
3. django-debug-toolbarのSQLパネルを使う


#### BP5 select_related / prefetch_relatedでクエリ本数を減らす

N+1問題を回避する。モデルでリレーション先のデータを取得するときに使う。

|METHOD|NOTE|
|---|---|
|select_related|「一」や「多」側から「一」のオブジェクトをJOINで取得|
|prefetch_related|「一」や「多」側から「多」のオブジェクトを取得してキャッシュに保持|

```python
Book.objects.all().select_related('publisher')
SELECT * FROM book INNER JOIN publisher ON book.publisher_id = publisher.id
```

```python
Book.objects.all().prefetch_related('authors')
```


#### BP6 ベーステンプレートを用意する

テンプレートの共通部分(headタグやbodyタグ前のJavaScript)はbase.htmlに書いて、各テンプレート内で継承する。

```bash
`-- templates
    |-- accounts
    |   `-- login.html
    `-- base.html
```


#### BP7 こんなときはModelFormを継承しよう

通常のフォームが継承しているdjango.forms.Formの代わりにdjango.forms.models.ModelFormを継承することで、特定のモデルのフィールド定義を再利用できる。デフォルトのフォームバリデーションの他にモデルのバリデーションが走る。

```python[accounts/forms.py]
from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
  class Meta:
    model = User
    fields = ('username', 'email', 'password',)
    widgets = {
      'password': forms.PasswordInput(attrs={'placeholder': 'パスワード'}),
    }
  password_confirm = forms.CharField(
    label='パスワード確認',
    required=True,
    strip=False,
    widget=forms.PasswordInput(attrs={'placeholder': 'パスワード確認'}),
  )

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['username'].widget.attrs = {'placeholder': 'ユーザー名'}
    self.fields['email'].required = True
    self.fields['email'].widget.attrs = {'placeholder': 'メールアドレス'}

  # ユニーク制約チェック
  def clean(self):
    super().clean()
    password = self.cleaned_data['password']
    password_confirm = self.cleaned_data['password_confirm']
    if password != password_confirm:
      raise forms.ValidationError('パスワードとパスワード確認が合致しません')
```

```python[accounts/views.py]
form = RegisterForm(request.POST)
# save
user = form.save()
# or
user = form.save(commit=False)
user.set_password(form.cleaned_data['password'])
user.save()
```


#### BP8 メッセージフレームワークを使う

フラッシュメッセージとも言う。MessageMiddlewareを使う。startproject
したときにデフォルトで有効化されている。デフォルトではCookieを使う設定になっているが、Cookieだとリダイレクトしたときにメッセージが表示されない場合があるのでSessionを使うように変更する。

```python[config/settings.py]
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
```

```python[accounts/views.py]
from django.contrib import messages
from django.urls import reverse
from django.views import View

class LoginView(View):
  def post(self, *args, **kwargs):
  ...
  messages.info(request, "ログインしました。")

  return redirect(reverse('item:index'))
```

templatesディレクトリに_message.htmlを作成する。

```python[templates/_messages.html]
{% if messages %}
<div class="ui relazed divided list">
  {% for message in messages %}
  <div class="ui {% if message.tags %}{{ message.tags }}{% endif %} message">
    {{ message }}
  </div>
  {% endfor %}
</div>
{% endif %}
```


#### BP9 個人の開発環境の設定はlocal_settings.pyに書く

このリポジトリでは開発環境用(docker-compose.yml)と本番環境用(docker-compose.prod.yml)で環境を分割しているので省略。ちなみに『現場でDjango』の構成は以下。

```bash
config/settings
|-- __init__.py
|-- base.py
|-- local.py
|-- production.py
`-- test.py
```

#### BP10 シークレットな変数は.envファイルに書く

パスワードなどの機密性の高い変数はGit管理下に置かない。現場でDjangoはdjango-environパッケージを使っているが、このリポジトリではcontainerのOSに環境変数を設定している。上述の通り、開発環境と本番環境でdocker-compose.yml(container)を分けているでこのリポジトリでは使わない。


## Setup environment

1. Make Pipfile
2. Install pipenv and packages

```bash[bash]
cd app
pip install pipenv
pipenv install
pipenv shell
(app) django-admin.py startproject config .
(app) python manage.py migrate
(app) python manage.py runserver
```

## Setup docker

1. Make Dockerfile for Django
2. Make dokcer-compose.yml for Django

## Update settings.py

1. SECRET_KEY
2. DEBUG
3. ALLOWED_HOSTS

## Start via docker-compose

```bash[bash]
docker-compose up -d --build
```

## Setup postgres

1. Add postgres service in docker-compose.yml
2. Update .env for postgresql
3. Update settings.py
4. Update Dockerfile for psycopg2

Up docker-compose and migrate. So we can see welcome page on localhost:8000.

```bash[bash]
docker-compose down -v
docker-compose up -d --build
docker-compose exec django python manage.py migrate
```

### Setup auto migrate

1. Add entrypoint.sh
2. chmod +x entrypoint.sh
3. Update Dockerfile

```bash[bash]
chmod +x app/entrypoint.sh
```


## Setup Gunicorn

1. Add gunicorn in Pipfile
2. Add docker-compose.prod.yml and update
3. Add entrypoint.prod.sh
4. Add Dockerfile.prod
5. Update docker-compose.prod.yml for new Dockerfile.prod
6. CMD and check localhost:8000/admin

```bash[bash]
docker-compose down -v
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate --noinput
```


## Setup Nginx

1. Make nginx dir to root
2. Add Dockerfile
3. Add nginx.conf
4. Add nginx in docker-compose.prod.yml
5. Check connection of nginx

```bash[bash]
docker-compose down -v
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate --noinput
```


## Setup static file

1. Update settings.py
2. Update entrypoint.sh for collectstatic command
3. Update docker-compose.prod.yml for staticfiles
4. Update nginx.conf for staticfiles

```bash[bash]
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec django python manage.py collectstatic
```
