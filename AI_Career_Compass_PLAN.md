# Current implementation direction — 2026-09-21 revision

The user requested a guided, personal and more interactive experience for students who are unfamiliar with AI job searching. The primary flow is now a four-step profile, plain-language role discovery, evidence-based matching, skill/location what-if scenarios, and a downloadable exploration plan. The job directory, comparison and data charts remain supporting tools.

Collection expands nationwide using official employer sources, with prior career research used only for discovery. Explicit new-grad, zero-experience, 0–2-year and unclear-eligibility groups remain distinct. Missing experience is never zero. Profile information stays in the browser. The actual submission repository is `https://github.com/zhaotianyu0702/mit-1.125-ps1`, rooted locally in `ps1/`.

The original planning details below are historical; this revision, the data contract and the implemented methodology take precedence where scope differs.

---

# AI Career Compass — US New Grad AI Roles

规划日期：2026-09-21。状态：产品与实施规划，尚未构建网站或完成全量采集。

已确定范围：仅做 AI Career Compass；面向全美国的 new grad AI 岗位。截止时间按作业提供的 09/22 17:00 安排，提交前核对课程时区。

## 1. 产品定位与完成目标

**一句话定位：帮助大学职业中心和学生社群，用有来源的公开招聘数据，为应届毕业生筛选、理解和比较美国 AI 岗位。**

主要使用者是本科、硕士和博士应届毕业生；组织用户是大学职业中心与学生社群。网站不把个人背景当作全站规则，不默认只看硕士、湾区或 LLM training。

网站回答四个问题：

1. 当前采集到的美国 AI new grad 机会在哪里、属于哪些方向？
2. 在学历、毕业窗口、经验和工作地点条件下，哪些岗位值得进一步查看？
3. 这些岗位的核心职责、技能要求、薪资披露和申请条件有什么区别？
4. 这些数据支持哪些求职搜索建议，哪些结论仍无法确定？

成功标准：用户能从首页开始，在三分钟内完成筛选、理解一条岗位的纳入依据、比较两到三条岗位并打开官方申请页面；教师能直接找到数据、方法、发现、建议、反思与演示材料。

网站主体使用英文，便于课程展示和面向美国求职场景；本规划使用中文。

## 2. 范围与判定规则

### 2.1 地域、雇佣类型与毕业周期

- 纳入明确列出美国工作地点、Remote — US，或允许选择美国地点的多地点职位。城市与州标准化；明确的美国领地单独标注。美国与海外混合地点的职位标记 mixed geography，并只把已确认的美国地点纳入美国分布图。
- 仅写 Remote、没有说明是否可在美国工作的职位进入待核实清单，不进入默认美国机会统计。
- Remote 职位保留州限制、居住要求和原文。Remote 不自动等于全美任意地点可工作。
- 纳入全职、面向毕业生的技术岗位。排除实习、co-op、postdoc、兼职、contract、转正仅限既有实习生的封闭通道和人才社区占位页；性质不明则待核实。
- 默认展示采集时仍有官方申请入口的毕业生岗位；区分毕业窗口与入职窗口。2026、2027、未说明作为首批常用筛选，其他明确年份保留，不把年份硬编码为永久范围。
- 标题中的 “2027 Start” 是入职年份，不自动当作毕业年份。

### 2.2 New grad 判定

| 状态 | 判定依据 | 展示与统计规则 |
| --- | --- | --- |
| Explicit new grad | 官方标题、正文或有明确关联的 graduate recruiting program 明确欢迎应届毕业生 | 经人工核实后进入主列表与默认统计；必须继续展示学历和经验条件 |
| Explicit zero-experience pathway | 无明确 new grad 标签，但完整 JD 明确存在允许零全职行业经验的资格路径，例如 0–2 years / no prior professional experience required | 经人工核实后可作为独立可开关分组；不混称为明确校招职位 |
| Unclear | 只有 junior、associate、early career 标签，未说明经验；或资格存在无法解释的冲突 | 只保留在采集与排除记录，不进入默认列表与分析 |
| Not eligible for scope | 所有资格路径均明确要求已有全职经验，或属于排除的职位类型 | 排除并记录原因 |

默认选择 Explicit new grad；用户可主动加入明确允许零经验的相邻机会。统计标题始终显示当前口径。

**不能将学历和经验分别摊平。** 每个岗位保存一组或多组资格路径，例如 `Bachelor + 2 years industry experience OR Master/PhD`。选择硕士后，只能依据硕士对应路径解释条件。实习、课程项目、研究经验和全职行业经验分开记录。

标题中的 Senior/Staff 是审查信号，不单独决定排除；如果官方明确接受 PhD new grad，保留该博士路径，并醒目标注。反过来，标题写 New Grad 也不能覆盖正文中的硬条件。

真实设计样例（本轮阅读官方页面，仅用于解释规则）：

- [NewsBreak — Software Engineer, ML Infra (Junior & New Grad)](https://job-boards.greenhouse.io/newsbreak/jobs/4615879006)：学历与经验存在替代路径，说明不能只读标题。
- [PlusAI — Senior Machine Learning Engineer, Perception](https://jobs.lever.co/plus-2/d1b8ecc2-dfc2-4613-81ca-02d90776c618)：页面明确提到 PhD new grad 或硕士加行业经验，说明不能只凭 Senior 一词删除。

这些链接仍需在正式数据冻结时重新核查，不能将规划阶段访问视为交付时仍开放的证明。

### 2.3 AI 岗位定义与分类

核心职责必须涉及模型研发、训练、评估、推理、部署、AI 应用或直接支持模型工作的基础设施。不能因为公司是 AI 公司，或 JD 出现“使用 AI 工具提高效率”，就认定为 AI 岗位。

每个岗位只给一个主要职能类别，以便分类图可加总；技术方向可多选。

| 主要职能 | 纳入示例 |
| --- | --- |
| Machine Learning Engineering | 推荐、搜索、预测、视觉、语音等模型开发与落地 |
| AI / LLM Application Engineering | LLM 应用、RAG、agent、AI 产品后端；AI 是核心职责 |
| Research Scientist / Research Engineer | AI/ML 算法与实验研究，保留 Scientist/Engineer 原始标题差异 |
| ML Infrastructure / MLOps | 模型训练系统、推理系统、模型服务、ML platform |
| Applied Data Science | 以 ML 建模和实验为核心的应用科学/数据科学岗位 |

多选技术标签：LLM、post-training、inference、distributed training、recommendation/search、CV、robotics、speech、evaluation 等。它们是筛选维度，不另做 Training vs. Inference 产品。

排除纯 BI/报表、普通数据分析、没有明确 ML 工作的通用 data engineering、销售、产品运营和与 AI 职责无关的 SWE。

## 3. 用户流程与信息架构

建议四个顶层入口：`Explore Jobs`、`Market Insights`、`Compare & Saved`、`Data & Methodology`。职位详情用侧栏或详情页，保持筛选状态。作业材料集中在 Data & Methodology。

主要流程：

`选择学历/毕业窗口与地点 → 查看筛选结果 → 打开岗位证据 → 加入比较或收藏 → 打开官方申请页`

分析流程：

`查看样本概况 → 调整同一套筛选 → 点击图表细分 → 查看对应岗位 → 阅读有证据的求职建议`

首页第一屏包含一句话目的、采集日期、关键筛选、结果数与实际岗位；不安排占据大屏的宣传封面。

## 4. 功能规划

### 4.1 Explore Jobs：核心工作界面（P0）

**基础筛选：**

- Keyword：搜索职位、公司和技能，不只搜索标题。
- Degree pathway：Bachelor / Master / PhD / Equivalent / Not stated。默认不限制学历。
- Graduation window 与 Start window：分别筛选，并保留未说明项。
- Location：州、城市/metro、Remote — US；默认全美。
- Role family：上述五类。
- New grad evidence：明确校招 / 加入明确零经验路径。

**展开的高级筛选：**

- Company、技术方向、技能、工作方式。
- 经验要求及其种类；允许只看零全职行业经验可满足的路径。
- 已披露年度 USD base salary 区间；未披露薪资默认保留，开启薪资筛选时可明确选择是否排除。
- Sponsorship statement：explicitly supported / explicitly not offered / conditional / not stated；只能使用岗位原文。
- 明确申请截止时间；无截止时间不能标成“长期开放”。

同一维度多选取 OR，跨维度取 AND。所有未知字段有明确标签和处理说明，不静默按否处理。默认保留未说明项并单独标注；用户可切换仅显示明确满足已选条件的岗位。

显示已选条件 chips、清空筛选、结果总数、去重公司数、当前数据快照时间。空结果解释是哪组条件产生零结果，并提供逐项撤回，不自动放宽学历或地域。

**岗位卡片/表格列：**

公司、岗位、美国地点/工作方式、主要类别、new grad 依据、学历与经验路径摘要、毕业/入职窗口、已披露薪资区间、最后核查日期、收藏、比较。

默认不设黑箱匹配分。排序以已核查状态和可解释字段为基础：公司、职位、已知截止日、有效发布日期、已披露薪资。没有真实发布日期时不以抓取时间冒充“刚发布”。

### 4.2 岗位详情与证据（P0）

- 职责与要求的结构化摘要，保留原始标题。
- “Why this is included”：AI 职责证据、new grad 证据、美国地点证据。
- 资格路径：必需学历、经验类型与年限、毕业窗口、允许的替代路径；必需与 preferred 分开。
- Required / Preferred / Mentioned skills；“PyTorch or TensorFlow”保留二选一含义，不改成两项均必须。
- 薪资按地区、币种、周期显示；base、bonus、equity 不混合。
- 工作方式、公开 sponsorship 原文、截止日、来源链接、采集/核查时间。
- `View official posting` / `Apply on company site`；网站本身不收申请信息。
- 对已选择筛选条件显示“符合已披露条件 / 有条件需确认 / 存在明确冲突”，每条解释都可追溯。它不是资格认证或录取概率。

### 4.3 Market Insights：数据分析（P0）

所有视图使用同一个经过验证、去重的筛选结果集。顶部固定显示 `n postings / m companies`、采集日期、主要口径和关键缺失率。

| 视图 | 用户可作出的判断 | 口径与交互 |
| --- | --- | --- |
| 机会概况指标 | 样本中有多少有效职位、多少家公司、多少明确校招岗位 | 计数为招聘广告/职位记录，不是招聘人数；点击进入列表 |
| 地域分布条形图 | 当前筛选下哪些地点值得扩大搜索 | 每个地点统计包含该地点的去重职位；地区之间可能重叠，不能加总；Remote 单列 |
| 职能类别分布 | 当前条件下有哪些岗位方向 | 每岗位一个主要职能；同时显示涉及公司数，点击过滤 |
| 学历与资格路径比较 | 哪些机会明确向本科/硕士/博士毕业生开放 | 一个岗位可有多个路径；列出路径重叠说明与 unknown，不暗示三类互斥 |
| 技能 × 职能热力图（P1） | 不同职位方向常提到什么技能 | 以提及该技能的岗位数/该类有效 JD 数为单位；标注样本量；默认展示 required 与 preferred 的区分 |

优先实现概况、地域、职能、资格四组视图；技能热力图在提取质量通过后加入。即使数据不足，前三组与资格表仍足以满足至少三种分析展示。

**美国地图（P1）：** 可加州级交互地图，点击联动列表，配套可访问的条形图。没有采到的地区标“样本中未观测到”，不解释为没有岗位；不以公司总部替代工作地点；不把 remote 复制到所有州。

**薪资视图（P1）：** 仅在披露数据足够时展示按职位/地区的 base salary 区间点图，显示披露比例。少于 5 条可比记录的分组显示“样本不足”，不做薪资排行榜。不要把薪资区间中点称为平均实际工资，不将不同地区区间包成一个误导性的薪资区间。

### 4.4 Compare & Saved（岗位比较 P0；收藏 P1）

- 同时比较 2–3 个岗位：职责、地点、工作方式、学历/经验路径、毕业窗口、技能、薪资、sponsorship 声明、截止日、官方链接。
- 差异突出显示，未知项明确写 Not stated。
- 桌面为并列表；手机为按比较维度逐项展示，避免整页横向溢出。
- 收藏仅保存在当前浏览器；不需要账户，也不保存简历、姓名、联系方式或申请状态。
- 可导出当前筛选结果 CSV（P0）；收藏导出为 P1。下载应与当前筛选和排序对应，并包含快照日期和来源链接。
- URL 保存筛选条件（P1），便于向同学分享同一视图。收藏不放进公开 URL。

### 4.5 Findings & Recommendations（P0，放在 Insights 页面）

提供 3–4 条来自完整快照的主要发现、至少 2 条可操作建议。固定发现注明基于全体样本；如果另有筛选结果摘要，标为“当前筛选”，二者不混用。

每条建议必须包含：适用人群、观察到的数据与分母、建议行动、关联岗位或图表链接、限制条件。

可采用的建议结构，具体内容必须等数据分析后填写：

- “对于 [学历/毕业窗口] 的学生，扩展到 [地区/岗位类别]，可以在本样本中看到另外 [N] 条有明确资格依据的岗位，来自 [M] 家公司。”
- “针对 [岗位类别] 准备申请材料时，优先展示 [技能/项目类型] 的证据；该要求出现在 [n/N] 条相关 JD 中，涉及 [M] 家公司。”

第二类是求职准备建议，不引入 workshop 规划器、课程分配或技能组合优化功能。

不预写结论、不使用模拟百分比；没有证据支持两条普适建议时，给出范围更窄的分组建议并标注样本大小。

### 4.6 Data & Methodology（P0）

- 数据来源、采集流程、公司采样规则、日期、字段字典和分类定义。
- 下载 `jobs.csv`、`job_locations.csv`、`job_skills.csv`、`qualification_paths.csv`、`source_coverage.csv`。
- 解释主表一行一个去重岗位，其余文件保存一对多关系，避免重复计数。
- 一页方法说明：网页正文 + 可打印版本，覆盖数据来源、纳入/排除、去重、提取、分析、局限和复现方式。
- Reflection：数据支持什么、不支持什么、主要偏差、AI 辅助提取的人工验证、下一步如何改进。
- 五分钟演示稿与可在网站打开的演示材料。
- GitHub 仓库链接、版本/快照标识和更新说明。

## 5. 公开数据与采样计划

### 5.1 来源分层

1. 公开官方 ATS API：Greenhouse、Lever；Ashby 视可用性补充。
2. 公司官方 careers 页面与 graduate program 页面：补齐未使用这些 ATS 的公司。不能因接口不方便而整体忽略大型雇主或美国其他地区。
3. 公开 new grad 清单、GitHub 社区清单、搜索引擎：仅用于发现；正式记录必须回到官方职位页核实。

本轮已有证据：

- [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html)：官方说明 GET 不需认证；上一轮实际成功读取 Anthropic、Together AI 的公开接口。只能证明接口可用，不能证明这些公司的全部职位符合本项目。
- [Lever Postings API](https://github.com/lever/postings-api)：公开发布职位与 JSON 字段文档可用；具体公司接口需在采集阶段验证。
- [Ashby Public Job Posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)：提供职位、地点、工作方式和可选薪酬字段；当前环境访问实测 403，不能作为唯一依赖。只处理公开列出的 `isListed=true` 岗位。
- [ID.me — Summer 2027 Data Scientist (New Grad)](https://job-boards.greenhouse.io/idmeuniversityrecruiting/jobs/7986505003)：本轮查到有具体硕士毕业窗口的官方样例。正式记录需读取岗位特定地点，不把公司通用办公地点直接当成该岗位所有地点。

### 5.2 样本范围与数量目标

以 40–60 家公司的候选发现清单起步，覆盖大科技公司、AI 产品与基础设施公司、机器人/自动驾驶，以及有明确 AI 技术岗位的其他行业雇主。搜索按全国展开，不设湾区优先排序。

探索性目标是核实 20–40 家有合格岗位的公司、约 60–150 条合格职位；这是工作量估计，不是数据数量承诺或上线硬门槛。实际样本少就如实公布，不通过混入 senior-only、非美国或一般 SWE 来补数量。

`source_coverage.csv` 记录检查过的公司、官方来源、检查时间和结果：有合格岗位 / 无合格岗位 / 无法访问 / 待核实。无法访问不能记为零机会。

采样是有目的的公开岗位样本，不宣称全国完整覆盖。页面用 “US new grad AI roles in our sample”，不用 “All US AI jobs”。

## 6. 数据结构与证据保留

| 数据表 | 关键字段 |
| --- | --- |
| jobs | stable_job_id、company、title、source_platform、source_job_id、requisition_id、canonical_url、apply_url、employment_type、role_family、newgrad_status、status_at_check、published_at、updated_at、first_seen_at、verified_at、snapshot_id |
| qualification_paths | job_id、path_id、degree、equivalent_allowed、experience_min/max、experience_type、graduation_start/end、start_window、required/preferred、evidence |
| job_locations | job_id、location_id、city、state、country、metro、workplace_type、remote_scope、location_evidence |
| job_skills | job_id、skill、normalized_skill、required/preferred/mentioned、alternative_group、evidence |
| salary_ranges | job_id、location_scope、currency、pay_period、base_min/max、salary_type、evidence |
| evidence | job_id、field、source_url、short_excerpt、checked_at、review_status |
| source_coverage | company、official_url、checked_at、access_status、candidate_count、verified_count、exclusion_reason_summary |

公开数据不包括候选人或招聘联系人的姓名、邮箱、电话、个人位置、简历和申请表回答。只保存岗位主体的必要文本与证据；在持久化前去除联系信息与申请表字段。未经清洗的接口响应不提交到 GitHub 或下载区。

优先发布结构化事实、短证据摘录与原文链接，避免复制完整申请表或整站内容。

## 7. 采集、去重和验证流程

`来源发现 → 官方页面/接口读取 → 清洗与字段标准化 → 资格和 AI 职责提取 → 去重 → 人工证据核查 → CSV/JSON 快照 → 网站分析`

- 规则负责明显字段和硬条件；LLM 可辅助分类、技能归一化和摘要，但必须有原文依据，无法确定返回 unknown。
- 不需要上线聊天机器人或运行时模型 API；同一数据快照下，图表与筛选保持可复现。
- 去重优先采用公司 + requisition/internal job ID；其次 source job ID 与 canonical URL。去除 URL 的 tracking 参数。不能只按标题去重，不同 requisition 可有同名岗位。
- 跨 ATS、重复地点广告和转载记录需要关联；无法自动确认时人工审核，保留合并依据。
- 一个多地点岗位在全站总数计一次。地点图按“可在该地点申请的职位”计数，注明地区重叠；Remote 单列，不复制至全部州。
- HTTP 200 不等于仍在招聘。需要检查职位特定标题/ID、申请入口、关闭提示、是否重定向到通用招聘首页，以及官方 board 中是否仍存在。
- 所有进入主列表的岗位人工核实官方来源、美国地点、AI 职责、新毕业资格路径和状态。复杂学历分支、薪资地区分支、sponsorship 和标题/正文冲突逐条复核。
- 技能提取额外分层抽样检查至少 20 条或全量的 20%，取较大者但不超过总量；出现系统性错误后修正规则并复查受影响类别。
- 正式发布前重新核查纳入岗位，生成固定快照。已关闭记录从当前统计排除，保留变更记录；访问失败标 unknown，不自动推断关闭。
- `last verified` 是核查时间，`published` 是来源发布时间，`updated` 是来源修改时间，三者分别记录。

## 8. 分析与局限的统一口径

必须显式说明：

1. 公开招聘广告不等于招聘人数、团队规模、实际录取人数或成功概率。
2. 非概率样本与 ATS 可访问性会影响公司、地区、行业和职位分布；筛选公司不能支撑全国占比推断。
3. 缺失不等于否。未写学历/经验/薪资/sponsorship 均保留未说明。
4. 本次是时点快照，不能证明需求正在增长、某技能造成高薪，或某地区更容易拿 offer。
5. 学历替代路径和研究经验可能导致表面上相同的门槛不可比；优先给原文和具体条件。
6. 公司招聘模板可能重复技能词；每条岗位对同一技能最多计一次，并补充涉及公司数。
7. 地点与学历图可能多重归属，不能按百分比堆叠成互斥整体；主职能图才采用互斥分类。
8. Salary 是已披露 base 区间，非实际工资或 total compensation；披露样本存在选择偏差。
9. Sponsorship 仅呈现当前岗位公开声明，不从公司名气、历史签证记录或申请表提问推断。
10. “建议扩大搜索范围”是样本支持的搜索策略，不是搬家、教育投资或就业结果保证。

不加入伪精确的全国市场份额、趋势预测、录取概率或综合机会评分。

## 9. 视觉与移动端

- 桌面：筛选侧栏 + 结果主区 + 岗位详情面板；顶部短导航与数据日期。
- 手机：顶部搜索、可展开筛选抽屉、单列岗位卡、底部比较入口。图表有文字或表格替代。
- 视觉方向：清晰的数据工作台，深蓝/石墨色正文、蓝色主交互、单一强调色；不依赖颜色区分资格状态。
- 表格信息密度高但可读，主要文字约 16px，常用标签不低于 14px；200% 文本放大可用。
- 支持键盘、可见 focus、带标签的控件、图表 tooltip/文字数值、loading/empty/error 状态。
- 关键日期、unknown、分母和来源属于可见信息，不藏在 hover-only 交互里。
- 不使用装饰图片或生成图片；地图、图表和排版承担视觉表达。

## 10. 技术与仓库规划

推荐结构：本地脚本采集和验证，生成静态 JSON/CSV；前端读取固定快照并在浏览器完成筛选、比较和图表计算。这样教学展示不依赖现场招聘 API 或模型服务。

前端可用 React + TypeScript，采用适合 Sites 发布的静态输出；图表使用成熟组件。最终框架与依赖在实施时按 Sites starter 和项目现状确定，不为规划提前安装运行时。

建议目录：

```text
ps1/
  AI_Career_Compass_PLAN.md
  app/ or src/              # 网站代码，按实际 starter 确定
  scripts/                 # collect / normalize / validate / export
  data/
    sources/               # 来源清单、采样和核查日志
    snapshots/<date>/      # 清洗后的结构化快照、元数据
  public/downloads/        # CSV、方法说明、演示与反思
  docs/                    # 字段字典、标签规则、方法和演示源文件
  README.md
```

收藏和显示偏好仅存在本机浏览器；不需要数据库、登录、简历上传、自动投递、通知系统或云端个人资料。保留可复跑的数据脚本，暂不配置定时任务。

GitHub 保存代码、可发布数据快照和复现说明。网站有明确的快照日期，更新由重新采集、验证和发布触发。GitHub 与 Site 发布是后续实施交付步骤，本轮只完成规划。

## 11. 优先级、执行顺序与时间预算

| 级别 | 范围 | 完成判断 |
| --- | --- | --- |
| P0：完整作业版本 | 证据化数据集；全美/学历/毕业时间/职能筛选；列表与详情；2–3 岗位比较；至少 3 个分析视图；发现与 2 条建议；CSV/方法/反思/演示；移动端；GitHub 与发布 URL | 满足作业全部要求，能够演示一个完整决策流程 |
| P1：有余量再做 | 本地收藏、URL 分享、美国地图、经过验证的技能热力图、样本足够的薪资比较 | 不影响 P0 数据质量和发布时间 |
| 本轮不做 | Workshop 规划器、training-vs-inference 独立产品、登录、简历解析、AI 聊天、自动投递、申请 CRM、邮件推送、实时爬取、历史趋势 | 防止偏离用户明确选定的第一个产品 |

建议工作顺序与主动工时估计（非完成承诺）：

1. 30–45 分钟：确定公司采样清单和标签规则，先验证约 10 条跨学历/地域的岗位，检查数据是否足以支持图表。
2. 2–3 小时：扩展采集、去重和人工核查；同时冻结字段与组件契约。
3. 3–4 小时：核心界面、筛选、详情、比较、分析视图和移动端。
4. 1–2 小时：最终数据分析、两条实际建议、方法说明、反思与演示材料。
5. 1–1.5 小时：端到端验证、GitHub、发布和已发布页面检查。

如时间紧张，先缩小有证据的样本、移除 P1，不降低资格核查标准。建议至少在截止前 2 小时冻结数据和功能，最后 1 小时只处理发布、关键故障与提交链接。

可并行的执行子任务：按公司清单分片进行只读来源核查；按统一 schema 提取事实；独立审核数据与材料。主 Agent 维护统一标签规则、前端状态、集成、Sites 发布和验收，避免多人同时改共享界面。

## 12. 作业交付与演示

| 作业要求 | 对应产物 |
| --- | --- |
| 问题与目标用户 | 首页一句话说明 + Methodology |
| 数据采集说明、来源、日期、单位和定义 | Data & Methodology + 字段字典 |
| 至少三个有用分析展示 | 地域、职能、资格比较，附概况指标 |
| 筛选与比较 | Explore Jobs + Compare |
| 主要发现与至少两条实际建议 | Market Insights 下的 Findings & Recommendations |
| 缺失、偏差、不确定性和局限 | 每项分析的口径 + Methodology + Reflection |
| 电脑与手机 | 同一套响应式页面 |
| 数据 CSV | 网站下载区与 GitHub |
| 一页方法说明 | 可打印的一页文档及网站正文 |
| 五分钟展示 | 网站可打开的演示材料与讲稿 |
| 简短反思 | 网站 Reflection 与可下载文档 |
| Published Site + GitHub | 网站 URL、仓库链接；最后按课程要求提交到 PS1 栏 |

五分钟演示节奏：

- 0:00–0:40：说明毕业生面对的问题、组织用户和数据样本范围。
- 0:40–1:30：选择一个明确的学历/毕业窗口，展示全国到具体地点的筛选变化。
- 1:30–2:20：展示岗位的 new grad 依据与学历/经验组合条件。
- 2:20–3:10：比较两个岗位；解释为什么某个条件未知，需要回官方页面确认。
- 3:10–4:20：展示三种分析视图与两条来自数据的建议。
- 4:20–5:00：展示 CSV、方法、局限和 GitHub，说明数据不能证明什么。

## 13. 验收清单

### 数据

- 每个纳入岗位都有官方来源、美国地点、AI 职责、new grad/零经验依据、最后核查时间。
- 未明确接受新毕业生的普通 early-career 岗位不混入默认集合。
- 学历与经验按资格路径联合解释；实习和行业经验不混为一谈。
- 全国总数按岗位去重；多地点和多学历统计的重叠有说明。
- 关闭、通用招聘重定向、未列出或访问失败的岗位不冒充已验证在招岗位。
- 公开 CSV 与网站结果一致，所有 unknown 被保留，下载文件可重新读取。

### 功能

- 同一组筛选在列表、图表、计数和导出之间一致。
- 比较 2–3 个岗位、移除岗位、打开官方来源、下载文件可用。
- 清空筛选恢复基线；空结果和缺失字段可理解。
- 桌面和手机真实操作通过，关键控件支持键盘；无页面崩溃或明显横向溢出。
- 进行与风险相称的测试：资格路径、去重和统计一致性是重点；不为静态文案或样式写镜像测试。

### 交付

- 实际发布 URL 可访问；在已发布站点复查一个完整流程，而不只检查本地构建。
- 三个分析视图、两条实证建议、CSV、一页方法、演示、反思和 GitHub 链接均可打开。
- 方法说明实际打印/渲染为一页；若交 PDF 或 slides，检查最终文件显示结果。
- 结论文字与数据快照一致，没有示例数字、占位图或尚未实现的入口。

## 14. 当前默认决策与后续依赖

已按用户要求固定：只做第一个产品；全美国；聚焦 new grad AI roles。

可直接按以下默认继续设计：英文网站；覆盖本科/硕士/博士；毕业与入职窗口分开；默认严格 new grad；不收个人资料；采集时点快照；前端以筛选、证据和比较为核心。

实施阶段再决定：实际可验证样本数量、薪资与技能图是否数据充足、最终可用发布入口和 GitHub 仓库归属。上述依赖不影响当前产品规划，也不应靠虚构数据填补。
