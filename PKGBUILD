# Maintainer: Philipp Schmitt (philipp<at>schmitt<dot>co)

pkgname=pia-tools
pkgver=0.9.7.3
pkgrel=1
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
        'https://raw.githubusercontent.com/tempestnano/pia-tools/Single_user/pia-tools.install')
install="${pkgname}.install"

package() {
    cd "${srcdir}"
    install -Dm755 pia-tools "${pkgdir}/usr/bin/pia-tools"
    install -Dm644 pia-tools.groff "${pkgdir}/usr/share/man/man1/pia-tools.1"
    install -Dm644 pia@.service "${pkgdir}/usr/lib/systemd/system/pia@.service"
    install -Dm644 pia_common "${pkgdir}/etc/openvpn/pia/pia_common"
    install -Dm755 pia-up "${pkgdir}/etc/openvpn/pia/pia-up"
    install -Dm755 pia-up "${pkgdir}/etc/openvpn/pia/pia-down"
    install -Dm755 pia-up "${pkgdir}/etc/openvpn/pia/pia-route-up"
}
