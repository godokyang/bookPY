#!/bin/bash
echo "输入目标文件夹可批量解压rar文件"
pinc=/
endUrl=*.url
if [[ $1 ]]; then
    if [[ -d $1 ]]; then
        for file in `ls $1`; do
            # if [[ -d $file ]]; then
                for tRar in `ls $1$file|grep rar`; do
                    echo $1$file$pinc$tRar
                    echo $1$file$pinc$endUrl
                    unrar e $1$file$pinc$tRar $1$file$pinc
                    rm -rf $1$file$pinc$endUrl
                    #if [[ $? != 0 ]]; then
                    #    rm -rf $1$file$pinc$endUrl
                    #fi
                done
            # fi
        done
    else
        echo "不存在该目录"
    fi
fi
