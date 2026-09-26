# Licensing at gjl

Copyright (c) 2026 gjl. All rights reserved.

This repository contains public tools, agent skills, and installer scripts,
and distributes official gjl product release binaries. Different components
are covered by different licenses as described below:

- **Official Product Release Binaries**: Governed by the **gjl Product Binary License** (Section 1).
- **Tools, Skills, and Installer Scripts**: Governed by the **MIT License** (Section 2).
- **Public Documentation**: Copyright gjl, all rights reserved unless a file says otherwise.
- **Third-Party Open-Source Dependencies**: Listed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

---

## 1. gjl Product Binary License

Official release binaries available via [GitHub Releases](https://github.com/gjl-io/gjl/releases)
or official installer scripts are proprietary software governed by the following terms
(also available at [PRODUCT-LICENSE.md](PRODUCT-LICENSE.md)):

gjl grants you permission to download, install, and run unmodified official
gjl release binaries for your own personal use or your organization's
internal use, including user- or organization-operated Door, Gate, and Vault
deployments. You may only configure, store, or relay provider credentials,
API keys, and account sessions that are legally owned by, registered to, or
expressly authorized for you (for personal use) or your organization and its
internal personnel (for organizational use). No product account, license
server, paid-feature lock, or registration is required.

This permission does not grant rights to redistribute, sublicense, sell,
modify, reverse engineer, decompile, disassemble, or publish the product
binaries or private product source. Furthermore, you shall not use the product
binaries or relay deployments to broker, share, lease, resell, or distribute
third-party provider credentials, authenticated endpoints, or model access to
unauthorized third parties, or operate the product in any manner that violates
the terms of service, acceptable use policies, or licensing agreements of the
underlying LLM or service providers. Using the product for unauthorized
multi-tenant credential pooling, account resale, or credential sharing is
strictly prohibited. Get written permission from gjl before engaging in any
restricted activities. Rights that applicable law grants independently of this
license are unaffected.

Any use of the product binaries in breach of this license immediately and
automatically terminates your rights under this license.

The product is provided **as is**, without warranty of any kind, to the extent
permitted by applicable law. In no event shall gjl, its authors, or copyright
holders be liable for any direct, indirect, incidental, special, exemplary, or
consequential damages (including, but not limited to, third-party provider
account suspensions, terminations, or service disruptions; procurement of
substitute goods or services; loss of use, data, or profits; or business
interruption) however caused and on any theory of liability, whether in
contract, strict liability, or tort (including negligence or otherwise) arising
in any way out of the use of this software, even if advised of the possibility
of such damage.

The MIT license for the public tools and agent skills in this repository does not
apply to the gjl product binaries or private source.

---

## 2. Tools, Skills, and Installer Scripts (MIT License)

The public installer scripts (`install.sh`, `install.ps1`), Python files under
[`tools/`](tools/), and agent skills under [`skills/`](skills/) are licensed under the
MIT License below (also available at [LICENSE-MIT](LICENSE-MIT)):

### MIT License

Copyright (c) 2026 gjl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
