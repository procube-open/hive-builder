Vagrant のインストール
===============================
vagrant プロバイダを使用する場合は vagrant をインストールしてください。
また、 vagrant-disksize プラグインもインストールしてください。


.. note::

    raspbian では vagrant プロバイダは利用できません。
    vagrant プロバイダを使用しない場合は vagrantをインストールする必要はありません。

.. note::

    OSごとにインストール手順が異なりますので、以下の該当する手順のみを実行してください。
    使用しているOSと異なるOSの手順を実行しないように注意してください。

Centos 7 の場合
----------------------------------------
Centos 7 では vagrant の libvirt プロバイダを使用します。
libvert, qemu-kvm と Vagrant がインストールされている必要があります。
以下のコマンドを root ユーザで実行して vagrant をインストールしてください。

::

    yum install qemu-kvm qemu-img libvirt virt-install git libvirt-devel gcc
    systemctl enable --now libvirtd
    yum install https://releases.hashicorp.com/vagrant/2.2.14/vagrant_2.2.14_x86_64.rpm
    sh -c 'echo echo 5.2.30r130521 > /usr/bin/VBoxManage'
    chmod +x /usr/bin/VBoxManage

.. note::

    最後の2行は vagrant up で「Vagrant could not detect VirtualBox! Make sure VirtualBox is properly installed.」の
    エラーが出る場合に必要となる回避策です。Vagrant のバージョンによっては不要になる可能性があります。

.. note::

    2行目で「ファイルが開けません:  https://releases.hashicorp.com/vagrant/2.2.10/vagrant_2.2.10_x86_64.rpm を飛ばします。」というエラーが
    出る場合は、yum update nss curl コマンドを実行して、 nss と curl をアップデートしてください。

上記の後、構築を実行するユーザで以下のコマンドを実行して仮想環境を構築してください。

::

    vagrant plugin install vagrant-libvirt
    vagrant plugin install vagrant-disksize
    vagrant box add centos/8 --provider=libvirt
    sudo usermod --append --groups libvirt `whoami`

.. note::

    vagrant plugin installで「usr/bin/ld: 認識できないオプション '--compress-debug-sections=zlib' です」というエラーが
    出る場合は、以下のコマンドを実行して、vagrant にパッチをあててください。

    ::

        sudo sed -i -e 's/-Wl,--compress-debug-sections=zlib //' /opt/vagrant/embedded/lib/ruby/2.6.0/x86_64-linux/rbconfig.rb

Centos 8 の場合
----------------------------------------
Centos 8 では vagrant の libvirt プロバイダを使用します。
libvert, qemu-kvm と Vagrant がインストールされている必要があります。
また、 vagrant-disksize プラグインがインストールされている必要があります。
以下のコマンドを root ユーザで実行して vagrant をインストールしてください。

::

    yum install -y --enablerepo=powertools dnsmasq qemu-kvm qemu-img git gcc ruby ruby-devel cmake libcmocka-devel \
      libcmocka wget make gcc-c++ rpcgen python3-docutils ninja-build glib2-devel gnutls-devel \
      libxslt-devel libtirpc-devel yajl-devel byacc
    python3 -m venv ~/meson
    source ~/meson/bin/activate
    pip install meson
    wget https://github.com/libvirt/libvirt/archive/v6.10.0.tar.gz
    wget https://gitlab.com/keycodemap/keycodemapdb/-/archive/master/keycodemapdb-master.tar.gz
    tar xzf v6.10.0.tar.gz
    tar xzf keycodemapdb-master.tar.gz
    ln -s  ~/keycodemapdb-master/* libvirt-6.10.0/src/keycodemapdb/
    cd libvirt-6.10.0/
    groupadd libvirt
    chgrp -R libvirt /var/log/libvirt
    sed -i -e "s/^SELINUX=enforcing$/SELINUX=disabled/g" /etc/selinux/config
    setenforce 0
    meson --prefix=/usr --localstatedir=/var --sharedstatedir=/var/lib -D driver_qemu=enabled build
    ninja -C build
    ninja -C build install
    systemctl enable virtnetworkd libvirtd virtqemud virtstoraged
    dnf install -y https://releases.hashicorp.com/vagrant/2.2.14/vagrant_2.2.14_x86_64.rpm
    cd /tmp; wget https://vault.centos.org/8.3.2011/BaseOS/Source/SPackages/krb5-1.18.2-5.el8.src.rpm
    rpm2cpio krb5-1.18.2-5.el8.src.rpm | cpio -imdV
    tar xf krb5-1.18.2.tar.gz
    cd krb5-1.18.2/src
    LDFLAGS='-L/opt/vagrant/embedded/' ./configure
    make
    cp lib/libk5crypto.so.3.1 /opt/vagrant/embedded/lib64/
    ln -s libk5crypto.so.3.1 /opt/vagrant/embedded/lib64/libk5crypto.so.3
    ln -s libk5crypto.so.3.1 /opt/vagrant/embedded/lib64/libk5crypto.so
    cd /tmp; wget https://vault.centos.org/8.3.2011/BaseOS/Source/SPackages/libssh-0.9.4-2.el8.src.rpm
    rpm2cpio libssh-0.9.4-2.el8.src.rpm | cpio -imdV
    tar xf libssh-0.9.4.tar.xz
    cd libssh-0.9.4
    mkdir build; cd build
    cmake -DOPENSSL_ROOT_DIR=/opt/vagrant/embedded/ ..
    make
    cp lib/libssh.so.4.8.5 /opt/vagrant/embedded/lib64/
    ln -s libssh.so.4.8.5 /opt/vagrant/embedded/lib64/libssh.so.4
    ln -s libssh.so.4 /opt/vagrant/embedded/lib64/libssh.so
    sh -c 'echo echo 5.2.30r130521 > /usr/bin/VBoxManage'
    chmod +x /usr/bin/VBoxManage

.. note::

    CentOS Stream release 8 で vagrant 2.2.14 を安定して動作させるためには libvirt, libk5crypto, libssh をソースコードからビルドして
    インストールする必要があります。バイナリ配布されているlibvirt-6.0.0-29 では、vagrant up 時に Waiting for domain to get an IP address...
    のメッセージの後、ストールする場合があり、利用できません。また、 vagrant に付属のlibcrypto.so は CentOS 8 のものと
    互換性がなく「symbol EVP_KDF_ctrl version OPENSSL_1_1_1b not defined in file libcrypto.so.1.1 」というエラーが
    libk5cryptoとlibsshのロード時に発生し、利用できません。したがって、こちらもソースコードからビルドする必要があります。
    この手順は将来のバージョンで必要なくなる可能性があります。


.. note::

    最後の2行は vagrant up で「Vagrant could not detect VirtualBox! Make sure VirtualBox is properly installed.」の
    エラーが出る場合に必要となる回避策です。Vagrant のバージョンによっては不要になる可能性があります。

上記の後、構築を実行するユーザで以下のコマンドを実行してvagrantのプラグインをロードしてください。

::

    sudo usermod --append --groups libvirt `whoami`
    vagrant plugin install vagrant-libvirt vagrant-disksize
    vagrant box add centos/8 --provider=libvirt
    # stream-8 を使う場合
    # vagrant box add centos/8 https://cloud.centos.org/centos/8-stream/x86_64/images/CentOS-Stream-Vagrant-8-20200113.0.x86_64.vagrant-libvirt.box

WSL（Windows Subsystem for Linux）の場合
----------------------------------------------
WSL 上では vagrant の virtualbox プロバイダを使用します。
VirtualBox を公式サイト https://www.virtualbox.org/に従って Windows にインストールしてください。
その後以下のコマンドで WSL に Vagrantをインストールしてください。

::

    wget https://releases.hashicorp.com/vagrant/2.2.4/vagrant_2.2.16_x86_64.deb
    dpkg -i vagrant_2.2.16_x86_64.deb
    vagrant plugin install vagrant-disksize

Mac OS の場合
----------------------------------
Mac OS では vagrant の virtualbox プロバイダを使用します。
VirtualBox を公式サイト https://www.virtualbox.org/に従ってにインストールしてください。
その後以下のコマンドで Vagrantをインストールしてください。

::

    brew cask install vagrant
    vagrant plugin install vagrant-disksize

.. note::

    Mac OS では vagrant の libvirt プロバイダは動作しません。
    もし、vagrant-libvirt プラグインが入っている場合はアンインストールしてください。
