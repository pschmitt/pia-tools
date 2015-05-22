# Maintainer: Philipp Schmitt (philipp<at>schmitt<dot>co)

pkgname=pia-tools
pkgver=0.9.7.4
pkgrel=7
pkgdesc='OpenVPN hook for privateinternetaccess.com'
arch=('any')
url='https://github.com/pschmitt/pia-tools'
license=('GPL3')
depends=('transmission-cli' 'dnsutils' 'openvpn' 'systemd' 'sudo' 'wget' 'ufw' 'unzip' 'sed')
source=('https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-tools'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-tools.groff'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia@.service'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia_common'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-up'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-down'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-route-up'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia_common_single_user'
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-tools.install')
md5sums=('7a49a36bbf4ef6d54596e681685d390a'
         'b3fa2a6f12c6067bcb0024e54e25cf92'
         'f74962b853215b88b54bad3dad9ba004'
         '621f9228ba793b4307b354e92b8918c1'
         'f25f00fe408f31e50d46d69a597c6ece'
         '0ed5cf87b2853f9688c9df1dfe19b061'
         '3aa6dffb97bfb02a719c56b53de5658a'
         '80724ce4e66d14e2fef83edae778df0c'
         '24f69e9eea41a1247a974c7d5d3d9c30')
install="${pkgname}.install"

package() {
    cd "${srcdir}"
    install -Dm755 pia-tools "${pkgdir}/usr/bin/pia-tools"
    install -Dm644 pia-tools.groff "${pkgdir}/usr/share/man/man1/pia-tools.1"
    install -Dm644 pia@.service "${pkgdir}/usr/lib/systemd/system/pia@.service"
    install -Dm644 pia_common "${pkgdir}/etc/openvpn/pia/pia_common"
    install -Dm755 pia-up "${pkgdir}/etc/openvpn/pia/pia-up"
    install -Dm755 pia-down "${pkgdir}/etc/openvpn/pia/pia-down"
    install -Dm755 pia-route-up "${pkgdir}/etc/openvpn/pia/pia-route-up"
    install -Dm644 pia_common_single_user "${pkgdir}/etc/openvpn/pia/pia_common_single_user"
}
