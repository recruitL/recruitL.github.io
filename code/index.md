---
title: 代码库
lang: zh-CN
lang_pair: /en/code/
feature_text: |
  代码实现、论文复现和个人工具整理
feature_image: "https://raw.githubusercontent.com/recruitL/recruitL.github.io/main/document/picture/1300_400.jpg"
excerpt: "代码库入口"
aside: true
---

这里整理公开代码、实验脚本、论文复现和个人工具。

## GitHub

{% include button.html text="访问 GitHub" icon="github" link="https://github.com/recruitL" color="#0366d6" %}

## 项目列表

<table class="site-table">
  <thead>
    <tr>
      <th>仓库</th>
      <th>方向</th>
      <th>状态</th>
      <th>链接</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>py-sc</strong></td>
      <td>Python 数值计算课程型代码库</td>
      <td>第二章“数据插值”第一轮系统建设完成</td>
      <td><a href="https://github.com/recruitL/py-sc">GitHub</a></td>
    </tr>
  </tbody>
</table>

## py-sc

py-sc 按书籍章节组织理论笔记、Notebook、示例脚本和可复用实现。当前第二章“数据插值”覆盖插值基本形式、Lagrange/Newton 插值、Runge 现象、Chebyshev 节点、分段线性插值和自然三次样条插值，并保留 Hermite、PCHIP、B 样条与二维插值的后续扩展入口。

{% include button.html text="查看 py-sc" icon="github" link="https://github.com/recruitL/py-sc" color="#0366d6" %}

## 整理方式

* 每个仓库保留用途、状态、依赖环境和入口文档。
* 科研相关代码优先补充复现路径、测试数据和参考文献。
* 教程型代码按章节维护，避免脚本散落在博客正文里。
