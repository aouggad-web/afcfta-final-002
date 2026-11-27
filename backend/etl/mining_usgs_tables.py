"""
Minerais africains dérivés des fiches USGS MCS — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===============================================================================
Produit par ``backend/scripts/build_mining_from_usgs_pdfs.py`` depuis les
fiches par minerai des Mineral Commodity Summaries 2024, 2025, 2026
(https://pubs.usgs.gov/periodicals/mcs<édition>/).

46 commodités, 433 points, années 2022-2025. Chaque valeur est
un couple (valeur, édition MCS qui la publie) : la plus récente édition qui
publie l'année pour ce pays. La dernière année d'une édition est son estimation.

Sans aucun pays africain au tableau de production : Lead, Nickel, Antimony, Silver.
Ces commodités n'ont pas de série : l'USGS range leurs producteurs africains
dans « Other countries ».

Régénérer :
    python3 backend/scripts/build_mining_from_usgs_pdfs.py
"""

from __future__ import annotations

from typing import Dict

URL_FICHE = 'https://pubs.usgs.gov/periodicals/mcs{edition}/mcs{edition}-{slug}.pdf'

#: Empreinte SHA-256 de chaque fiche lue. Une régénération qui en change une
#: signale une révision de l'USGS — donc une relecture, pas un simple rafraîchissement.
USGS_PDF_SHA256: Dict[str, str] = {
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-antimony.pdf': '7b154b1e40ed371a06736e74014b434b35dfc38d567a84ace63df29584d0fc42',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-arsenic.pdf': 'e1aa2f35bfd8d5578b9abec0ea33dcd113a5f1e9fc11c63649c780dd0416d311',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-barite.pdf': '3425b1ec186fb1ec3bd1ea7ff2274f9470229ab62e216eb9f7338aa64f8fb82f',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-bauxite-alumina.pdf': '7311769aa95c70026d5739cd8856f1b4314063d78c352e7cf32375fb23da9134',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-beryllium.pdf': '7f831b1b5ec7edf9a43fb174e85ef9e958add981931a05229b2d44cb72936fee',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-cement.pdf': '979ea2c6daa3261deda4b402135ac2e6a8a81f9e75370cd180dc3438ed854622',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-chromium.pdf': '8b35f9b4cadb59b61527414944a5d04a68771834c224a5e3d502eb4258a9dd35',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-cobalt.pdf': '7cea74b82fdf6f3228a6111ac5b33e9d0d23364b491b976a44e6fa828f366e33',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-copper.pdf': '582f9135384885ccb004a724787fd55f751c057b616312f43a6078aaa6f52f69',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-diamond.pdf': 'ddff850584a5df5b763e521967c760bdc82e58d07eedae6012a6dac154902403',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-diatomite.pdf': '64319b2436963cd6d1dfa9ed086bf491afb09d0514a491f85285d3ac92e9785b',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-feldspar.pdf': '793a0700152d1438a423deb6d4427f55f96e915776bd87d6de8bc25fd0d9b08d',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-fluorspar.pdf': '4500d4b002fac46ee755ce8ed6fa3ba0ac0a948b5e897ad97792b8eea4d020e2',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-garnet.pdf': '371abe7cf6e1562687056bed7298d3e37ab94836a98f0eab56f2332743889d16',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-gemstones.pdf': '8bae2e692c8d32c5f76295ad5d38c09ec1dcb11a464b65e8389c31c335df7dc4',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-gold.pdf': '3b551dcc4dbc7e21b3b1789c4552dab12d370e7a839288744196105e4767946c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-graphite.pdf': '00ab8511468509f87a1b9b5d9393d5c172b3877cd3f7036304e122025c1b9742',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-gypsum.pdf': '1f3837071199a6a054ee2f7b7502491a1ad85602a9e07cb7710f0732bca93f53',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-helium.pdf': '07f70b812e89b1527d7a0cdc2b07a435b082396176cfa9c4b1ecb9afae904e6f',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-iron-ore.pdf': '8e3671f58e95f090050fa33eac7ccc4c1ae1764a3d8863659f8a982ddd9e65ac',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-lead.pdf': '2ed2d41936e7e9953a2cc20597b2485ef763aeef57d7c5e3966b893678a243e5',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-lime.pdf': '9a4f51bd1fc85efba1fd5e66bd6f2e65831adc5f49ed4daeaa8eadba4d414ec6',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-lithium.pdf': '14f43f30f8905f7cd3e6284a843fa007d74d0bf74f8ad186c7ae1219c115eb8b',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-manganese.pdf': 'c5b90e373a0e61b86176a337f8db8beac74683af8acc138437bd49c5da78748c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-mercury.pdf': '892a505a5cb177d41ced79680ed025c9846bf58b2e4f3b9d317975c37121b40e',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-mica.pdf': 'c8bd5fab2361095682177499229f0bf8ad60f54a89438d4c7a52917211be83bb',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-nickel.pdf': '39f5aa8333e52385861dab8e184d36be57b276246f343848ec46ea2e06a9f5cf',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-niobium.pdf': '9b62a06f97f5f378b5f5326e92eebc17057d307f98f4c3378c6c0583eb4b07fa',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-nitrogen.pdf': '503bca89df6be21833f655aebfaa1d66165c887abc65c3840c192890ba395971',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-perlite.pdf': '1b41c97c1fce3b1606b4868efdfeba2b7f28d42cde0cf4926c968ac2533a7653',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-phosphate.pdf': '65eac9e41af333fa72ce8de8147442de6b3fc31732aa7b9cc74380402e2fa26a',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-platinum-group.pdf': 'f05241d70dab46d401fdf58c5a60331e37ebed8ef51b2070d506c5403723de17',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-pumice.pdf': '59f7f19953435d083790603325b9f144a9c9de77632f28817049bf642b1a5c23',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-rare-earths.pdf': '1cc18fa276ff10cc05fdbe3ece4d003fafec58dd796582b36e7f2adfc15fc06b',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-salt.pdf': 'abe3e445614c59a2dd4a019a9af542690dd83d5149541fc75bf12b30e2eb38d2',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-selenium.pdf': '504f556493010291428ee1b02e4b169ed66b8dacb75e8fe39623db66861f4d23',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-silicon.pdf': '6dc5eabc728d7dfe0d741780e696d47bf222a2c7c7ab3587a7a8e955562027b6',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-silver.pdf': '7c74bb6f756c5b801882a487aac1053d1791af2d91a20c4fbc260ca678d72336',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-soda-ash.pdf': '4c6ca450215688a0669900292c6ae7b878ceb1e0749249e473cf81198ad3ea46',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-talc.pdf': 'fa61eb21a7560dff5dfb7395837fb7b9417cd1ce9dd9ee4dc2eb9ab7091553ed',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tantalum.pdf': 'c1a582c8467fb6a607c933e0ba7ddec2fae894b6a4f0183f86d3add5d5acee4c',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tellurium.pdf': '9bcd68ab71eb51c8325ef31c88748138b53b1b150cefbf0cc6835ac4968b5eab',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tin.pdf': '81ea9ab53ca494719f59993db111f718d8401fa9f66acb04606c45a7b947b979',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-titanium-minerals.pdf': 'a93112fd1dc3101607995a1fc637a151d3de2c2ccae2a245dc84d329c7c64b3d',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-tungsten.pdf': 'b2b196f7dcf3fefd2a32698f97f9e344eb7730911b9cb7ad0e1e4058e6995ed5',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-vanadium.pdf': '3a2d8f5e742646f82e8ef35816ebdd036374357c1cd551329faead800f6df5fc',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-vermiculite.pdf': 'fb21225cf258ab55ac89b64fb566e583847a9415039cd6bd58d11c0b38dada5d',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-zinc.pdf': 'cc889d5f180bf905564f678dae3d25d3018b9a67ca5de436d874b913ab68a841',
    'https://pubs.usgs.gov/periodicals/mcs2024/mcs2024-zirconium-hafnium.pdf': '6ee6c0c2ab7ce998f007ee9429368b5b8fdab27486c54e2fca27687b8d48e2c1',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-antimony.pdf': '9e79e0d2e45be3d9322ac77b48849420090c1ef90e07534419e45f531ff60c76',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-arsenic.pdf': '9690385f6def8858dd2ce6025a009213a738e1c5f7701da00c9b102fdc0b7e3a',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-barite.pdf': 'f4d5c02ff373e651c7b2c370d113c230e890e1a4a0d3cec28ac6f7dc4fc41274',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-bauxite-alumina.pdf': 'f37ce33c9b54976deb3ed22571fd2dfaa1f7c19dff174ff62b73105b0d81f189',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-beryllium.pdf': 'daa6bd33179d00da2ad76f9a104ae2a19d4a5c1ae825633217814a9e8a1153d5',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-cement.pdf': '57560e2e5eea8cfcdd1fdbd59fd8833add1097f9d53aec2a9c0f2d87cfaac334',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-chromium.pdf': '650dc3db07128f7233a0d730c31b67d782e78e6276ce7ec2e95fb2e13630b3b7',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-cobalt.pdf': '2d736a1d4f76a38b067c0b530d2db9121cdfe1d2b9c5b7d5c2343b7e6abc0d92',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-copper.pdf': '348b1e224d830a51e6d35cf81343eead26a0cb2a4e74c474d699b7faed1b10e6',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-diamond.pdf': '29ac1f6c9d4bcb640f3047e32690f9ffcb4efbbf84d094b302de9bebbeadc02c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-diatomite.pdf': '0912fd53878e35e958b6c1df90667e9423bc961d23747639644dbb0bcf69b439',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-feldspar.pdf': '3ec7a89e771fb0a534abb2cc68784d251b939660d028881a1bd82bb5da1c9326',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-fluorspar.pdf': '35384613f8fa6bc77ed69ae05688bdea3f61ddf98ea5571a65ff029f3a4f04d0',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-garnet.pdf': '4cce674bfe561be126716168ed5600688a8f87153784afac1ea31fa6a157c617',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gemstones.pdf': '66d406faa95c7dd6a79240cfdbef5dc5e5f92b9bce5c3799af821eeaaf5595c7',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gold.pdf': 'd4ec1750249005b4ad91dd59aaa7978932ecb7b7a410d8f6a135e6f8f8cc136f',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-graphite.pdf': '96f088e1346022462def556b9b470e0b14c290be496d4580ec0e1f93f2b88d88',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-gypsum.pdf': '0f3eac0c44547e9d10d98d717663facf62876a649a1f236e312f83520e736798',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-helium.pdf': '211bf4707cb97d0bfc8c6c8d5d19f55e7145534503a90d6d12b87c7786d67492',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-iron-ore.pdf': '5338c109340fd9d0edbde03c7fe17d2ab1632e7b47638850a705f5fca342d9c8',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lead.pdf': '2c02af206d1efab6f44d6f2d404df7c48936e30344830e18706ffcfedd8992ed',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lime.pdf': '0855c314c9e11fa32e12551877dfe16c586e30c210b0e67eb64bfcb813aa1774',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-lithium.pdf': '7ec5654133aa5ef64fcfd6d4d23ac64a58f06f51bf1231576ebd8f595ad9257b',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-manganese.pdf': '5868e111d64cc6a771883efd27332511ad407db64eddbe7c5f70a2256ecd2052',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-mercury.pdf': '3c3edbda9e6aafae619c6473a1b4a0b7e7877abf86ae0c97801eb1a2f92f35b1',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-mica.pdf': '339369e4b8ab8600abbf5d034afffc6f4ce78e966cffdceb20ad9858c44cd887',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-nickel.pdf': 'ad0eabdf50cd4d63a5c110ab1445697127c9c33e42eb4dca64135e4183d7d410',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-niobium.pdf': 'b0274f510aff379f984b2723dae2299c4bf25af32d2db5a835e9b3b5d801a607',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-nitrogen.pdf': 'aef2434040b06857a7fe93ae6b686eae744e8da9da61bec42711aaa292bf1a6d',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-perlite.pdf': 'c3ddf0e7a229adc1a15f9d90a51a1d4cb82e86a0bf65ec414e8e37c56a814da6',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-phosphate.pdf': '1680ad2ff3c481b5413a9ae686eed9c6a7ac72662373370ffa7f8ce311c36631',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-platinum-group.pdf': 'e2a443b26d93fc71431a26e094bc1630b220059f81c469db510266011aa4f376',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-pumice.pdf': '84b08c49f31a432bf783bdd5f85683bb72942fd4a25b3f47622eb88a93195232',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-rare-earths.pdf': '87e73bd28fd9d87b99a2ea58d104d6e41467e3488c181c61161e0abf22c6c7a1',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-salt.pdf': '2c5bbbdd435f1fd29f1acbc2806bcf2b2f80eb1490a72f4f08af3583f0b8cd0d',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-selenium.pdf': '9f353921833704827c622608549bbbea0bd671b8b008b3817d3142791735cfbe',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-silicon.pdf': '3f875a93b8455d18d25ce05c149cab493c8776e023ffa0388ea68658230ae66c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-silver.pdf': '1aa6e68c9700f88e97d4cbf31fc039d45d4b1b738a09f6bfece8edac0ec59b24',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-soda-ash.pdf': 'a386ee59806756e28c72f2fde95eaa3b68068e0614f1e0228fd13007be920ff5',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-talc.pdf': 'bb018f39eedace3bc9aafbed358e61e355e318fcba9862a0d6d63d6224ba0ada',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tantalum.pdf': 'd6f3e9e79fc10e5f4a20b277be4488c5e98484a830ef19c1888f37dc2d3a359c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tellurium.pdf': '18b5c86759c37e31f4ed31a664b0c6394d77a9040028446e995b2c2518bf09e8',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tin.pdf': 'dee3fdd3dff310c5e609e2ae069da2a5141dac471b0523b0c33217d1ac6b0e8d',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-titanium-minerals.pdf': '96a5d6922275b3a50f7515ae8e7283ca41477d9c0536dd62c6400ad04cc3df4c',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-tungsten.pdf': '73ea02e06e3f7a1dd6b61f40b9c89355e5be8a730d506121703e470ea25f8c02',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-vanadium.pdf': 'e9412dbb57fbead5d3bc410170517d794567bb20626717a7ac2184a1f3c9760b',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-vermiculite.pdf': 'cd21ea3b2a59ce58a5e71c7777852b7829dfd57c9184221a85fad18933301046',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-zinc.pdf': 'e99d72f809ed9ee8a2aa2b78339e13f91577ea36efb1a73a9df715df6aa0b9bc',
    'https://pubs.usgs.gov/periodicals/mcs2025/mcs2025-zirconium-hafnium.pdf': 'b7615a849825bb8947b71037e9fd634b288c4abadd188091f774b96078fb174c',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-antimony.pdf': '18c4498ac13ecd988439d7c78fb951d18498b172eea578b36f665a991720ca0d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-arsenic.pdf': '2344d21a385e4fada4d5e0f81c48391604963e46c04c259236a54793178eceb3',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-barite.pdf': '78c4191315efe0a1ec006a34fe115fdbcc530d43529fff32c843a58a7ccc1377',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-bauxite-alumina.pdf': 'ffc39426bfd2b1da97aa98080316cff077fda202ba004b9584301ee76cda1b5d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-beryllium.pdf': 'dee2faa35a4a824d04f37cf74e732074a315e8d541efc14d78d458f9ac9f317a',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-cement.pdf': 'b5412ccc0b314b48d31ae7aa4e6ee9521d38ff99fe15f38815de1a6ae8e3f98d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-chromium.pdf': 'c19e412f65eddf60ab8b3b49ec415d7e0b817d08412733a0094a47af06fa4a04',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-cobalt.pdf': 'cdfe86c808872800d8877b8af4a16d67822939a995b73960b419b2ceedb39fb3',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-copper.pdf': 'c4971f7edfa38feefc51952c5f24889c46f468d936c6620d388233313ae8ae85',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-diamond.pdf': 'b80adb50e11d2d5f80479dbb14e471955c2cd4866aefb863e277dec84683081e',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-diatomite.pdf': 'ca44f90d6ab2b690c1c79643c80fb864dacade2b501ef4711de9b14426467da1',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-feldspar.pdf': '1c7e9e569eeeb170636c5c4bd6d55f9863937260ff22d86d1c15a8059e2c1334',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-fluorspar.pdf': '7cb5aa4a162fadf72f77aa60ec9f2adb38e83e548d797ad6393e9c015c6822eb',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-garnet.pdf': '20b0c0af04c7cb8901ec073df8df95441b8c5b44c40af33ca80c6e990bf2c82a',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gemstones.pdf': 'ba51b1e6271d61048db49ccd9bc7acc5a254073d747fa68ec2c865556ed313f7',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gold.pdf': 'c2fef62f665d3334302b8b9bd32e2da6f40b3f8136d1ae00ffa102e196943627',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-graphite.pdf': '09ec621ed6400162e7f0b09b1e0ae8260a976d968c1936d69592fe5347f8df38',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-gypsum.pdf': '7519f016a1cacd09843fa4950a1a154c65864c46eb1f88118bfda25c8e0795b8',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-helium.pdf': 'e7c806d3768c8a349f9ba7d0444c32458dd48dab52b652c08e8e3edd8e0a3efa',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-iron-ore.pdf': 'd7f2919c4f003e101e2dddbec321904fd60c8e460adb0f2ac9013afc306045aa',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lead.pdf': '7abd4936108c47b9f240e7282579a917a052c72624b3ddf62ac8746926c2c46c',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lime.pdf': '814dabf93efa65cff92d5a1cb3d1cfcbc8667c01a0caff70de8b112009ddde28',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-lithium.pdf': '53f92ea45c367c36f05919151f7784feda5776095afaf3a25aec795a27be106f',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-manganese.pdf': '05e4fc710af04302a9cfecb2802d926943940c7421c419b5c6501fba0ff34ff5',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-mercury.pdf': '7b7983d655b15e8aabcdf0173de8e0d052fd51e9969cbbcdf7f92040654059f2',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-mica.pdf': 'f7909d5b47c573e1d4d82f7a2f6f45289c4777590bbbfd14aa246a82ccf8dc01',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-nickel.pdf': '70aab7644bc8b43fb9eef4d3a3e007186a9be6958dd476e3747a96e3c9d5de3c',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-niobium.pdf': 'c4b8bcabd89012891f7473fadceac6c7d76bdcf38df4f0cc02950db8387da72d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-nitrogen.pdf': '5d405858aadef2982f6de705059dfd7f9dc0cd408088113f0e8cef7445edac58',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-perlite.pdf': '17c7b06e4045f45000fbb6fd64973e134a79d35eb84dbf0a0595ccc4d4519e05',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-phosphate.pdf': '6aec496668eb9d9e5483a2ce23caa28f94a1201b64b75453965c35879200a4fc',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-platinum-group.pdf': 'e28369fb9be476bb46e1d7eee3d9d6ef184985db4c7b05b0c145e383b88fd35d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-pumice.pdf': '30fe51c3c25d3c7bb83cfec75f18394d97c6e1bd3ffd75c4a8f893b84e516cc2',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-rare-earths.pdf': '0116a192336fec41c38d8e11dad553bb7703308c1fbd1f97dc14b75c7e7d9900',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-salt.pdf': 'eb75608168f69761dd27cbcafbc6bcbf131855ad7c1ec108c5f6f20fff72838d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-selenium.pdf': '7d98d4bbb1960b77b04be16276d2370b0a9a05af7e6bd58cd71d9b49ce48ea4d',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-silicon.pdf': '985d56cd7c66234380753f75b75b753aca9d7f2f133483ce80a4699ef8ac2dcd',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-silver.pdf': 'f0dfe407304855a51f7647fc711f6c32081188a86269d011cd45e297aa673855',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-soda-ash.pdf': '13642c68a895cd3fd263f78539287932489a5601ad31f691e8732b70989d4728',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-talc.pdf': '1b2073688971e094047919feacef5bb22bba9ef5b68fd021a05a8e1d86c54573',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tantalum.pdf': 'ddcfdf129bf67c2cced06f8476ec24937ac4f0f995d2ac7354a582f35491c1bf',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tellurium.pdf': '9207db697705244bfdac9812aa81cfefa0e7fe61a9936431136f05dff4f4ee74',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tin.pdf': '659ee022301fcd3eda08f4ac22c8f33030c11ed0dca9851306e18c745d29a017',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-titanium-minerals.pdf': '4c71412fae1ec452e1cc82869f4aaaa15640ed38fb576cfb8e6b741a024ad185',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-tungsten.pdf': 'c33271f3529cc546707c05c7d02c34c9cd321772dbcbb3e787c7715dcb889847',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-vanadium.pdf': '8ffc21c8a35caeec5ae3b12298b14aa20dbd1cc618b0c9d388ab1f5010c321ef',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-vermiculite.pdf': 'c13e0911eb047c764aa4840427eaf0bebaa9e9bfde1e157e9955adda9da042bb',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-zinc.pdf': '81f42c706a239392df03b26134cfffbafaaecc81193d7f3b1071f3eb68d40eca',
    'https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-zirconium-hafnium.pdf': '6a1196f46b40d676871990f1e4165230f099c7a250b64c0893699ec9943ea1e5',
}

#: commodité -> {slug, unit, measure, by_country: {iso3: {année: (valeur, édition)}}}
MCS_TABLES: Dict[str, dict] = {
    'Gold': {
        'slug': 'gold',
        'unit': 'tonnes',
        'measure': 'Mine production, gold content',
        'by_country': {
            'BFA': {2022: (58.0, 2024), 2023: (57.0, 2025), 2024: (60.0, 2025)},
            'GHA': {2022: (88.0, 2024), 2023: (126.0, 2025), 2024: (149.0, 2026), 2025: (150.0, 2026)},
            'MLI': {2022: (64.0, 2024), 2023: (67.0, 2025), 2024: (70.0, 2025)},
            'TZA': {2022: (57.0, 2024), 2023: (55.0, 2025), 2024: (60.0, 2025)},
            'ZAF': {2022: (89.0, 2024), 2023: (104.0, 2025), 2024: (90.0, 2026), 2025: (90.0, 2026)},
        },
    },
    'Copper': {
        'slug': 'copper',
        'unit': 'tonnes',
        'measure': 'Mine production, copper content',
        'by_country': {
            'COD': {2022: (2350000.0, 2024), 2023: (2930000.0, 2025), 2024: (2990000.0, 2026), 2025: (3200000.0, 2026)},
            'ZMB': {2022: (797000.0, 2024), 2023: (712000.0, 2025), 2024: (823000.0, 2026), 2025: (940000.0, 2026)},
        },
    },
    'Cobalt': {
        'slug': 'cobalt',
        'unit': 'tonnes',
        'measure': 'Mine production, cobalt content',
        'by_country': {
            'COD': {2022: (144000.0, 2024), 2023: (175000.0, 2025), 2024: (226000.0, 2026), 2025: (230000.0, 2026)},
            'MDG': {2022: (3500.0, 2024), 2023: (4000.0, 2025), 2024: (3100.0, 2026), 2025: (3900.0, 2026)},
        },
    },
    'Diamonds': {
        'slug': 'diamond',
        'unit': 'carats',
        'measure': 'Mine production, natural industrial diamond',
        'by_country': {
            'AGO': {2022: (1000000.0, 2024), 2023: (1000000.0, 2025), 2024: (1000000.0, 2026), 2025: (1000000.0, 2026)},
            'BWA': {2022: (7000000.0, 2024), 2023: (8000000.0, 2025), 2024: (5000000.0, 2026), 2025: (5000000.0, 2026)},
            'COD': {2022: (8000000.0, 2024), 2023: (7000000.0, 2025), 2024: (7000000.0, 2026), 2025: (7000000.0, 2026)},
            'ZAF': {2022: (6000000.0, 2024), 2023: (4000000.0, 2025), 2024: (3000000.0, 2026), 2025: (3000000.0, 2026)},
            'ZWE': {2022: (4000000.0, 2024), 2023: (4000000.0, 2025), 2024: (5000000.0, 2026), 2025: (5000000.0, 2026)},
        },
    },
    'Phosphate': {
        'slug': 'phosphate',
        'unit': 'tonnes',
        'measure': 'Mine production, marketable phosphate rock',
        'by_country': {
            'DZA': {2022: (1800000.0, 2024), 2023: (2000000.0, 2025), 2024: (2000000.0, 2026), 2025: (2000000.0, 2026)},
            'EGY': {2022: (5000000.0, 2024), 2023: (5000000.0, 2025), 2024: (5300000.0, 2026), 2025: (5500000.0, 2026)},
            'MAR': {2022: (39000000.0, 2024), 2023: (33000000.0, 2025), 2024: (35300000.0, 2026), 2025: (36000000.0, 2026)},
            'SEN': {2022: (2600000.0, 2024), 2023: (2400000.0, 2025), 2024: (2800000.0, 2026), 2025: (2800000.0, 2026)},
            'TGO': {2022: (1500000.0, 2024), 2023: (1610000.0, 2025), 2024: (1560000.0, 2026), 2025: (1600000.0, 2026)},
            'TUN': {2022: (3560000.0, 2024), 2023: (3600000.0, 2025), 2024: (3280000.0, 2026), 2025: (3300000.0, 2026)},
            'ZAF': {2022: (1990000.0, 2024), 2023: (1720000.0, 2025), 2024: (2220000.0, 2026), 2025: (2200000.0, 2026)},
        },
    },
    'Bauxite': {
        'slug': 'bauxite-alumina',
        'unit': 'tonnes',
        'measure': 'Mine production, bauxite, dry tons',
        'by_country': {
            'GIN': {2022: (100000000.0, 2024), 2023: (123000000.0, 2025), 2024: (142000000.0, 2026), 2025: (150000000.0, 2026)},
        },
    },
    'Iron ore': {
        'slug': 'iron-ore',
        'unit': 'tonnes',
        'measure': 'Mine production, usable ore',
        'by_country': {
            'MRT': {2022: (12700000.0, 2024), 2023: (14100000.0, 2025), 2024: (14300000.0, 2026), 2025: (15000000.0, 2026)},
            'ZAF': {2022: (63700000.0, 2024), 2023: (63200000.0, 2025), 2024: (64000000.0, 2026), 2025: (66000000.0, 2026)},
        },
    },
    'Manganese': {
        'slug': 'manganese',
        'unit': 'tonnes',
        'measure': 'Mine production, manganese content',
        'by_country': {
            'CIV': {2022: (394000.0, 2024), 2023: (357000.0, 2025), 2024: (340000.0, 2026), 2025: (350000.0, 2026)},
            'GAB': {2022: (4670000.0, 2024), 2023: (4490000.0, 2025), 2024: (4640000.0, 2026), 2025: (5000000.0, 2026)},
            'GHA': {2022: (844000.0, 2024), 2023: (818000.0, 2025), 2024: (1280000.0, 2026), 2025: (2000000.0, 2026)},
            'ZAF': {2022: (7300000.0, 2024), 2023: (7300000.0, 2025), 2024: (7490000.0, 2026), 2025: (7600000.0, 2026)},
        },
    },
    'Platinum': {
        'slug': 'platinum-group',
        'unit': 'tonnes',
        'measure': 'Mine production, platinum',
        'by_country': {
            'ZAF': {2022: (124.0, 2024), 2023: (125.0, 2025), 2024: (126.0, 2026), 2025: (120.0, 2026)},
            'ZWE': {2022: (17.0, 2024), 2023: (19.2, 2025), 2024: (18.4, 2026), 2025: (18.0, 2026)},
        },
    },
    'Palladium': {
        'slug': 'platinum-group',
        'unit': 'tonnes',
        'measure': 'Mine production, palladium',
        'by_country': {
            'ZAF': {2022: (73.1, 2024), 2023: (74.9, 2025), 2024: (82.6, 2026), 2025: (70.0, 2026)},
            'ZWE': {2022: (14.3, 2024), 2023: (15.9, 2025), 2024: (15.2, 2026), 2025: (15.0, 2026)},
        },
    },
    'Zinc': {
        'slug': 'zinc',
        'unit': 'tonnes',
        'measure': 'Mine production, zinc content',
        'by_country': {
            'ZAF': {2022: (238000.0, 2024), 2023: (198000.0, 2025), 2024: (120000.0, 2025)},
        },
    },
    'Tin': {
        'slug': 'tin',
        'unit': 'tonnes',
        'measure': 'Mine production, tin content',
        'by_country': {
            'COD': {2022: (18600.0, 2024), 2023: (20000.0, 2025), 2024: (26000.0, 2026), 2025: (27000.0, 2026)},
            'NGA': {2022: (7000.0, 2024), 2023: (7000.0, 2025), 2024: (3100.0, 2026), 2025: (3500.0, 2026)},
            'RWA': {2022: (3300.0, 2024), 2023: (3600.0, 2025), 2024: (4100.0, 2026), 2025: (4600.0, 2026)},
        },
    },
    'Chromium': {
        'slug': 'chromium',
        'unit': 'tonnes',
        'measure': 'Mine production, marketable chromite ore',
        'by_country': {
            'ZAF': {2022: (19100000.0, 2024), 2023: (19700000.0, 2025), 2024: (22900000.0, 2026), 2025: (23000000.0, 2026)},
            'ZWE': {2023: (1070000.0, 2025), 2024: (1600000.0, 2026), 2025: (2000000.0, 2026)},
        },
    },
    'Lithium': {
        'slug': 'lithium',
        'unit': 'tonnes',
        'measure': 'Mine production, lithium content',
        'by_country': {
            'MLI': {2024: (770.0, 2026), 2025: (9400.0, 2026)},
            'NAM': {2023: (2700.0, 2025), 2024: (2700.0, 2025)},
            'ZWE': {2022: (1030.0, 2024), 2023: (14900.0, 2025), 2024: (20000.0, 2026), 2025: (28000.0, 2026)},
        },
    },
    'Graphite': {
        'slug': 'graphite',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'MDG': {2022: (130000.0, 2024), 2023: (63000.0, 2025), 2024: (85000.0, 2026), 2025: (80000.0, 2026)},
            'MOZ': {2022: (166000.0, 2024), 2023: (98000.0, 2025), 2024: (39000.0, 2026), 2025: (60000.0, 2026)},
            'TZA': {2022: (6120.0, 2024), 2023: (13200.0, 2025), 2024: (27000.0, 2026), 2025: (75000.0, 2026)},
        },
    },
    'Tantalum': {
        'slug': 'tantalum',
        'unit': 'tonnes',
        'measure': 'Mine production, tantalum content',
        'by_country': {
            'BDI': {2022: (59.0, 2024), 2023: (1.0, 2025), 2024: (2.0, 2026), 2025: (2.0, 2026)},
            'COD': {2022: (890.0, 2024), 2023: (920.0, 2025), 2024: (1270.0, 2026), 2025: (1300.0, 2026)},
            'ETH': {2023: (40.0, 2025), 2024: (40.0, 2026), 2025: (40.0, 2026)},
            'MOZ': {2023: (51.0, 2025), 2024: (55.0, 2026), 2025: (1.0, 2026)},
            'NGA': {2022: (110.0, 2024), 2023: (390.0, 2025), 2024: (390.0, 2026), 2025: (390.0, 2026)},
            'RWA': {2022: (347.0, 2024), 2023: (350.0, 2025), 2024: (374.0, 2026), 2025: (400.0, 2026)},
        },
    },
    'Vanadium': {
        'slug': 'vanadium',
        'unit': 'tonnes',
        'measure': 'Mine production, vanadium content',
        'by_country': {
            'ZAF': {2022: (8870.0, 2024), 2023: (8670.0, 2025), 2024: (8050.0, 2026), 2025: (5000.0, 2026)},
        },
    },
    'Titanium (ilmenite)': {
        'slug': 'titanium-minerals',
        'unit': 'tonnes',
        'measure': 'Mine production, ilmenite, TiO2 content',
        'by_country': {
            'KEN': {2022: (190000.0, 2024)},
            'MDG': {2022: (320000.0, 2024), 2023: (300000.0, 2025), 2024: (300000.0, 2026), 2025: (300000.0, 2026)},
            'MOZ': {2022: (1400000.0, 2024), 2023: (1860000.0, 2025), 2024: (1930000.0, 2026), 2025: (1900000.0, 2026)},
            'SEN': {2022: (410000.0, 2024), 2023: (260000.0, 2025), 2024: (345000.0, 2026), 2025: (370000.0, 2026)},
            'ZAF': {2022: (1100000.0, 2024), 2023: (1260000.0, 2025), 2024: (1260000.0, 2026), 2025: (1300000.0, 2026)},
        },
    },
    'Zircon': {
        'slug': 'zirconium-hafnium',
        'unit': 'tonnes',
        'measure': 'Mine production, zirconium mineral concentrates',
        'by_country': {
            'KEN': {2022: (27000.0, 2024), 2023: (20000.0, 2025), 2024: (20000.0, 2025)},
            'MDG': {2022: (27000.0, 2024), 2023: (34000.0, 2025), 2024: (31000.0, 2026), 2025: (26000.0, 2026)},
            'MOZ': {2022: (104000.0, 2024), 2023: (144000.0, 2025), 2024: (124000.0, 2026), 2025: (160000.0, 2026)},
            'SEN': {2022: (57000.0, 2024), 2023: (48000.0, 2025), 2024: (68000.0, 2026), 2025: (70000.0, 2026)},
            'SLE': {2022: (34000.0, 2024), 2023: (28000.0, 2025), 2024: (25000.0, 2026), 2025: (25000.0, 2026)},
            'ZAF': {2022: (300000.0, 2024), 2023: (289000.0, 2025), 2024: (290000.0, 2026), 2025: (270000.0, 2026)},
        },
    },
    'Fluorspar': {
        'slug': 'fluorspar',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'ZAF': {2022: (406000.0, 2024), 2023: (345000.0, 2025), 2024: (447000.0, 2026), 2025: (410000.0, 2026)},
        },
    },
    'Salt': {
        'slug': 'salt',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'EGY': {2022: (2300000.0, 2024), 2023: (2300000.0, 2025), 2024: (2300000.0, 2026), 2025: (2300000.0, 2026)},
        },
    },
    'Gypsum': {
        'slug': 'gypsum',
        'unit': 'tonnes',
        'measure': 'Mine production',
        'by_country': {
            'DZA': {2022: (2500000.0, 2024), 2023: (2500000.0, 2025), 2024: (2500000.0, 2026), 2025: (2500000.0, 2026)},
        },
    },
    'Arsenic': {
        'slug': 'arsenic',
        'unit': 'metric tons',
        'measure': 'Plant production, arsenic trioxide or calculated equivalent.',
        'by_country': {
            'MAR': {2022: (7500.0, 2024), 2023: (6000.0, 2025), 2024: (6000.0, 2026), 2025: (5000.0, 2026)},
        },
    },
    'Barite': {
        'slug': 'barite',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, barite, estimated',
        'by_country': {
            'MAR': {2022: (1200.0, 2024), 2023: (1000.0, 2025), 2024: (930.0, 2026), 2025: (1000.0, 2026)},
        },
    },
    'Beryllium': {
        'slug': 'beryllium',
        'unit': 'metric tons',
        'measure': 'Mine production, beryllium content',
        'by_country': {
            'MDG': {2022: (1.0, 2024), 2023: (1.0, 2025), 2024: (1.0, 2026), 2025: (1.0, 2026)},
            'MOZ': {2022: (25.0, 2024), 2023: (23.0, 2025), 2024: (3.0, 2026), 2025: (3.0, 2026)},
            'NGA': {2024: (40.0, 2026), 2025: (40.0, 2026)},
            'RWA': {2022: (1.0, 2024), 2023: (1.0, 2025), 2024: (1.0, 2026), 2025: (1.0, 2026)},
            'UGA': {2022: (1.0, 2024), 2023: (1.0, 2025), 2024: (1.0, 2025)},
        },
    },
    'Cement': {
        'slug': 'cement',
        'unit': 'thousand metric tons',
        'measure': 'Cement production, estimated',
        'by_country': {
            'EGY': {2022: (46000.0, 2024), 2023: (52000.0, 2025), 2024: (53000.0, 2026), 2025: (64000.0, 2026)},
        },
    },
    'Diatomite': {
        'slug': 'diatomite',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'MOZ': {2022: (73.0, 2024), 2023: (50.0, 2025), 2024: (50.0, 2025)},
        },
    },
    'Feldspar': {
        'slug': 'feldspar',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'MAR': {2023: (590.0, 2025), 2024: (720.0, 2026), 2025: (720.0, 2026)},
        },
    },
    'Garnet (industrial)': {
        'slug': 'garnet',
        'unit': 'metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2022: (179000.0, 2024), 2023: (180000.0, 2025), 2024: (40000.0, 2026)},
        },
    },
    'Gemstones': {
        'slug': 'gemstones',
        'unit': 'thousand carats',
        'measure': 'Mine production, thousand carats of gem-quality diamond',
        'by_country': {
            'AGO': {2022: (7890.0, 2024), 2023: (8780.0, 2025), 2024: (12600.0, 2026), 2025: (13000.0, 2026)},
            'BWA': {2022: (17100.0, 2024), 2023: (17600.0, 2025), 2024: (12700.0, 2026), 2025: (13000.0, 2026)},
            'COD': {2022: (1980.0, 2024), 2023: (1670.0, 2025), 2024: (1960.0, 2026), 2025: (2000.0, 2026)},
            'GHA': {2023: (203.0, 2025), 2024: (333.0, 2026), 2025: (330.0, 2026)},
            'GIN': {2022: (103.0, 2024), 2023: (96.0, 2025), 2024: (96.0, 2025)},
            'LSO': {2022: (728.0, 2024), 2023: (472.0, 2025), 2024: (696.0, 2026), 2025: (700.0, 2026)},
            'NAM': {2022: (2050.0, 2024), 2023: (2390.0, 2025), 2024: (2320.0, 2026), 2025: (2300.0, 2026)},
            'SLE': {2022: (551.0, 2024), 2023: (420.0, 2025), 2024: (459.0, 2026), 2025: (460.0, 2026)},
            'TZA': {2022: (319.0, 2024), 2023: (162.0, 2025), 2024: (318.0, 2026), 2025: (320.0, 2026)},
            'ZAF': {2022: (3860.0, 2024), 2023: (2360.0, 2025), 2024: (2140.0, 2026), 2025: (2100.0, 2026)},
            'ZWE': {2022: (446.0, 2024), 2023: (491.0, 2025), 2024: (529.0, 2026), 2025: (530.0, 2026)},
        },
    },
    'Helium': {
        'slug': 'helium',
        'unit': 'million cubic meters',
        'measure': 'Production, helium gas content',
        'by_country': {
            'DZA': {2022: (8.0, 2024), 2023: (9.0, 2025), 2024: (11.0, 2026), 2025: (11.0, 2026)},
        },
    },
    'Lime': {
        'slug': 'lime',
        'unit': 'thousand metric tons',
        'measure': 'Plant production, lime',
        'by_country': {
            'ZAF': {2022: (1070.0, 2024), 2023: (1100.0, 2025), 2024: (1000.0, 2026), 2025: (1000.0, 2026)},
        },
    },
    'Mercury': {
        'slug': 'mercury',
        'unit': 'metric tons',
        'measure': 'Mine production, mercury content',
        'by_country': {
            'MAR': {2022: (2.0, 2024), 2023: (2.0, 2025), 2024: (2.0, 2026), 2025: (2.0, 2026)},
        },
    },
    'Mica (Natural)': {
        'slug': 'mica',
        'unit': 'metric tons',
        'measure': 'Mine production, mica scrap and flake',
        'by_country': {
            'MDG': {2022: (35000.0, 2024), 2023: (63000.0, 2025), 2024: (90000.0, 2026), 2025: (70000.0, 2026)},
        },
    },
    'Niobium': {
        'slug': 'niobium',
        'unit': 'metric tons',
        'measure': 'Mine production, niobium content',
        'by_country': {
            'COD': {2022: (710.0, 2024), 2023: (740.0, 2025), 2024: (930.0, 2026), 2025: (970.0, 2026)},
            'RWA': {2022: (199.0, 2024), 2023: (210.0, 2025), 2024: (210.0, 2026), 2025: (200.0, 2026)},
        },
    },
    'Nitrogen(fixed) - Ammonia': {
        'slug': 'nitrogen',
        'unit': 'thousand metric tons',
        'measure': 'Plant production, nitrogen content',
        'by_country': {
            'DZA': {2022: (2600.0, 2024), 2023: (2000.0, 2025), 2024: (2000.0, 2026), 2025: (2000.0, 2026)},
            'EGY': {2022: (4100.0, 2024), 2023: (4500.0, 2025), 2024: (3900.0, 2026), 2025: (4000.0, 2026)},
            'NGA': {2022: (1600.0, 2024), 2023: (1700.0, 2025), 2024: (2000.0, 2026), 2025: (2000.0, 2026)},
        },
    },
    'Perlite': {
        'slug': 'perlite',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2023: (11.0, 2025), 2024: (11.0, 2026), 2025: (10.0, 2026)},
        },
    },
    'Pumice & Pumicite': {
        'slug': 'pumice',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'CMR': {2022: (280.0, 2024), 2023: (280.0, 2025), 2024: (370.0, 2026), 2025: (370.0, 2026)},
            'DZA': {2022: (900.0, 2024), 2023: (900.0, 2025), 2024: (900.0, 2026), 2025: (900.0, 2026)},
            'ETH': {2022: (510.0, 2024), 2023: (510.0, 2025), 2024: (510.0, 2026), 2025: (510.0, 2026)},
            'TZA': {2022: (220.0, 2024), 2023: (230.0, 2025), 2024: (350.0, 2026), 2025: (350.0, 2026)},
            'UGA': {2022: (1300.0, 2024), 2023: (830.0, 2025), 2024: (830.0, 2026), 2025: (830.0, 2026)},
        },
    },
    'Rare earths': {
        'slug': 'rare-earths',
        'unit': 'metric tons',
        'measure': 'Mine production, rare-earth-oxide equivalent',
        'by_country': {
            'MDG': {2022: (960.0, 2024), 2023: (2100.0, 2025), 2024: (1400.0, 2026), 2025: (2700.0, 2026)},
            'NGA': {2023: (7200.0, 2025), 2024: (1500.0, 2026), 2025: (1500.0, 2026)},
        },
    },
    'Selenium': {
        'slug': 'selenium',
        'unit': 'metric tons',
        'measure': 'Refinery production, selenium content',
        'by_country': {
            'ZAF': {2023: (9.0, 2025), 2024: (11.0, 2026), 2025: (10.0, 2026)},
        },
    },
    'Silicon': {
        'slug': 'silicon',
        'unit': 'thousand metric tons',
        'measure': 'Plant production, Ferosilicon, silicon content',
        'by_country': {
            'ZAF': {2023: (37.0, 2025), 2024: (36.0, 2026), 2025: (35.0, 2026)},
        },
    },
    'Soda ash': {
        'slug': 'soda-ash',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, natural',
        'by_country': {
            'BWA': {2022: (285.0, 2024), 2023: (262.0, 2025), 2024: (298.0, 2026), 2025: (290.0, 2026)},
            'ETH': {2022: (18.0, 2024), 2023: (18.0, 2025), 2024: (18.0, 2026), 2025: (18.0, 2026)},
            'KEN': {2022: (280.0, 2024), 2023: (300.0, 2025), 2024: (265.0, 2026), 2025: (270.0, 2026)},
        },
    },
    'Talc, crude': {
        'slug': 'talc',
        'unit': 'thousand metric tons',
        'measure': 'Mine production, estimated',
        'by_country': {
            'ZAF': {2022: (439.0, 2024), 2023: (200.0, 2025), 2024: (390.0, 2026), 2025: (300.0, 2026)},
        },
    },
    'Tellurium': {
        'slug': 'tellurium',
        'unit': 'metric tons',
        'measure': 'Refinery production, tellurium content',
        'by_country': {
            'ZAF': {2022: (4.0, 2024), 2023: (4.0, 2025), 2024: (5.0, 2026), 2025: (5.0, 2026)},
        },
    },
    'Tungsten': {
        'slug': 'tungsten',
        'unit': 'metric tons',
        'measure': 'Mine production, tungsten content',
        'by_country': {
            'RWA': {2022: (1400.0, 2024), 2023: (1200.0, 2025), 2024: (1300.0, 2026), 2025: (1300.0, 2026)},
        },
    },
    'Vermiculite': {
        'slug': 'vermiculite',
        'unit': 'thousand metric tons',
        'measure': 'Mine production',
        'by_country': {
            'UGA': {2022: (30.0, 2024), 2023: (23.0, 2025), 2024: (24.0, 2026), 2025: (20.0, 2026)},
            'ZAF': {2022: (183.0, 2024), 2023: (170.0, 2025), 2024: (163.0, 2026), 2025: (160.0, 2026)},
            'ZWE': {2022: (45.0, 2024), 2023: (28.0, 2025), 2024: (28.0, 2026), 2025: (30.0, 2026)},
        },
    },
}
