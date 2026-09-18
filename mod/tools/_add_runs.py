#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给 build.gradle 补 runs { client / server }，让 ForgeGradle 生成 runClient 任务。

FG6 不会自动建运行配置，官方 MDK 是显式声明的 —— 所以之前 `gradlew runClient` 报 Task not found。
"""
import io

P = 'build.gradle'
s = io.open(P, encoding='utf-8').read()

old = "minecraft { mappings channel: 'official', version: '1.20.1' }"
new = """minecraft {
    mappings channel: 'official', version: '1.20.1'

    // FG6 不会自动生成运行任务，要显式声明；这样 gradlew runClient 才能起开发客户端
    runs {
        client {
            workingDirectory project.file('run')
            property 'forge.logging.console.level', 'debug'
            mods {
                hexalunar_calamity {
                    source sourceSets.main
                }
            }
        }
        server {
            workingDirectory project.file('run')
            property 'forge.logging.console.level', 'debug'
            mods {
                hexalunar_calamity {
                    source sourceSets.main
                }
            }
        }
    }
}"""

if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('已补 runs 块')
elif 'runs {' in s:
    print('已经有 runs 块，跳过')
else:
    print('锚点未匹配！minecraft 块内容可能已变，需手工检查')
