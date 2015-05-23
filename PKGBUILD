# Maintainer: Philipp Schmitt (philipp<at>schmitt<dot>co)

pkgname=pia-tools
pkgver=0.9.7.4
pkgrel=9
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
md5sums=('a31103ee9b3dc171c44ed957200c2675'
         'b3fa2a6f12c6067bcb0024e54e25cf92'
         'f74962b853215b88b54bad3dad9ba004'
         '621f9228ba793b4307b354e92b8918c1'
         'cb9e0eb412089765d8a3083219f5c976'
         '55a668ce83f4d252ed4808408c0b9390'
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
