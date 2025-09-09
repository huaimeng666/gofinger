package main

import (
	"fmt"
	"os"

	"github.com/huaimeng666/gofinger/internal/checkenv"
	"github.com/huaimeng666/gofinger/internal/cmdline"
	"github.com/huaimeng666/gofinger/internal/config"
	"github.com/huaimeng666/gofinger/internal/initializer"
	"github.com/huaimeng666/gofinger/internal/logger"
	"github.com/huaimeng666/gofinger/internal/scanner"
	"github.com/huaimeng666/gofinger/internal/urlcollector"
)

func printBasicInfo() {
	green := "\033[32m"
	reset := "\033[0m"
	fmt.Printf("%sGOFinger: 红队资产指纹发现工具%s\n", green, reset)
	fmt.Printf("%sVersion: V0.6%s\n", green, reset)
	fmt.Printf("%sAuthor: huaimeng%s\n", green, reset)
	fmt.Printf("%sWebsite: https://github.com/huaimeng666/gofinger%s\n", green, reset)
}

func fatal(log *logger.Logger, msg string, err error) {
	// 只向标准错误输出流打印一次格式化的致命错误信息
	fmt.Fprintf(os.Stderr, "\n[致命错误] %s: %v\n\n", msg, err)
	os.Exit(1)
}

func main() {
	printBasicInfo()

	log := logger.NewLogger("info", "")

	cmdConfig, err := cmdline.Parse(log)
	if err != nil {
		fatal(log, "解析命令行参数失败", err)
	}

	log = logger.NewLogger(cmdConfig.LogLevel, cmdConfig.LogFile)

	// 在所有操作开始前，只打印一次代理信息
	if cmdConfig.Proxy != "" {
		log.Info().Str("proxy", cmdConfig.Proxy).Msg("检测到代理设置，将为所有网络请求应用此代理")
	}

	if cmdConfig.ShowHelp {
		os.Exit(0)
	}

	// 提前处理 -ut 更新命令
	if cmdConfig.UpdateTemplates {
		cfg, err := config.LoadConfig(log)
		if err != nil {
			fatal(log, "加载配置文件失败", err)
		}
		cmdConfig.ApplyToConfig(cfg, log)

		log.Info().Msg("正在强制更新所有库文件...")
		cfg.FingerPrintUpdate = true
		checkEnv := checkenv.NewCheckEnv(cfg, log)
		if err := checkEnv.UpdateLibraries(); err != nil {
			fatal(log, "库文件更新失败", err)
		}
		log.Info().Msg("所有库文件更新成功！")
		os.Exit(0)
	}

	// --- 正常扫描流程 --- 
	init, err := initializer.NewInitializer(cmdConfig, log)
	if err != nil {
		fatal(log, "初始化失败", err)
	}
	cfg, out, identifier, ipCache, _, req, apis, err := init.Initialize()
	if err != nil {
		fatal(log, "模块初始化失败", err)
	}

	// 根据配置检查和更新库文件
	checkEnv := checkenv.NewCheckEnv(cfg, log)
	if err := checkEnv.UpdateLibraries(); err != nil {
		fatal(log, "库文件检查失败", err)
	}

	collector := urlcollector.NewURLCollector(cfg, log, apis)
	urls, err := collector.CollectURLs(cmdConfig)
	if err != nil {
		fatal(log, "URL 收集失败", err)
	}

	if len(urls) == 0 {
		log.Warn().Msg("没有有效的 URL 可扫描")
		fmt.Fprintf(os.Stderr, "[警告] 没有有效的 URL 可扫描\n")
		os.Exit(0)
	}

	scanner := scanner.NewScanner(req, cfg, cmdConfig, identifier, log, out)
	scanner.Scan(urls)

	if cmdConfig.OutputFormat != "" {
		if err := out.Finalize(); err != nil {
			fatal(log, "完成结果保存失败", err)
		}
		log.Debug().Msg("结果已保存")
	}

	ipCache.Save()
}
