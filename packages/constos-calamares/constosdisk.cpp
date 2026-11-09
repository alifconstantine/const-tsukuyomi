// SPDX-License-Identifier: GPL-3.0-or-later
#include "GlobalStorage.h"
#include "JobQueue.h"
#include "utils/PluginFactory.h"
#include "viewpages/ViewStep.h"

#include <QFile>
#include <QFont>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QListWidget>
#include <QProcess>
#include <QPushButton>
#include <QStringList>
#include <QVBoxLayout>

class DiskStep : public Calamares::ViewStep
{
    Q_OBJECT

public:
    explicit DiskStep(QObject* parent = nullptr)
        : Calamares::ViewStep(parent)
    {
    }

    QString prettyName() const override { return tr("Disk"); }
    bool isNextEnabled() const override { return !selectedDisk().isEmpty(); }
    bool isBackEnabled() const override { return true; }
    bool isAtBeginning() const override { return true; }
    bool isAtEnd() const override { return true; }
    Calamares::JobList jobs() const override { return {}; }

    QString prettyStatus() const override
    {
        if (!isNextEnabled())
            return {};
        return tr("<strong>Use the entire disk %1</strong><br/>%2<br/>%3")
            .arg(m_disks->selectedItems().constFirst()->text().toHtmlEscaped(),
                 m_details->text().toHtmlEscaped(), layoutDescription().toHtmlEscaped());
    }

    QWidget* widget() override
    {
        if (m_page)
            return m_page;

        m_page = new QWidget;
        auto* content = new QWidget;
        content->setMaximumWidth(680);
        auto* pageLayout = new QVBoxLayout(m_page);
        pageLayout->setContentsMargins(16, 16, 16, 16);
        pageLayout->addWidget(content);
        pageLayout->addStretch();
        auto* layout = new QVBoxLayout(content);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->setSpacing(12);

        auto* title = label(tr("Choose an empty disk"));
        auto font = title->font();
        font.setBold(true);
        font.setPointSizeF(font.pointSizeF() * 1.3);
        title->setFont(font);
        layout->addWidget(title);
        layout->addWidget(label(tr("ConstOS uses the entire disk. Only fixed, empty disks of at least 32 GiB are shown.")));

        m_disks = new QListWidget;
        m_disks->setObjectName(QStringLiteral("target-disks"));
        m_disks->setSelectionMode(QAbstractItemView::SingleSelection);
        m_disks->setUniformItemSizes(true);
        m_disks->setMinimumHeight(104);
        m_disks->setMaximumHeight(176);
        m_disks->setAccessibleName(tr("Target disk"));
        auto* diskLabel = label(tr("&Target disk"));
        diskLabel->setBuddy(m_disks);
        layout->addWidget(diskLabel);
        layout->addWidget(m_disks);
        m_details = label({});
        layout->addWidget(m_details);

        layout->addSpacing(8);
        layout->addWidget(label(layoutDescription()));
        m_hint = label({});
        layout->addWidget(m_hint);

        m_refresh = new QPushButton(tr("Check &again"));
        layout->addWidget(m_refresh, 0, Qt::AlignLeft);
        auto* scan = new QProcess(m_page);
        connect(m_refresh, &QPushButton::clicked, this, [this, scan] {
            m_refresh->setEnabled(false);
            m_disks->clear();
            m_hint->setText(tr("Checking for eligible disks…"));
            scan->start(QStringLiteral("/usr/lib/constos-installer/backend.py"), {QStringLiteral("--scan-disks")});
        });
        connect(scan, &QProcess::finished, this, [this](int code, QProcess::ExitStatus status) {
            m_refresh->setEnabled(true);
            if (status == QProcess::NormalExit && code == 0)
                loadSnapshot();
            else
                m_hint->setText(tr("The disk check failed. Check again or use ConstOS Diagnostics."));
        });
        connect(scan, &QProcess::errorOccurred, this, [this](QProcess::ProcessError error) {
            if (error == QProcess::FailedToStart)
            {
                m_refresh->setEnabled(true);
                m_hint->setText(tr("Could not start the disk check. Use ConstOS Diagnostics."));
            }
        });
        connect(m_disks, &QListWidget::itemSelectionChanged, this, &DiskStep::updateSelection);
        loadSnapshot();
        return m_page;
    }

private:
    static QString layoutDescription()
    {
        return tr("GPT · EFI system partition (FAT32, 1 GiB) · Btrfs with @, @home, and @snapshots");
    }

    void loadSnapshot()
    {
        QFile input(QStringLiteral("/run/constos-installer/eligible-disks.json"));
        const auto snapshot = input.open(QIODevice::ReadOnly) ? QJsonDocument::fromJson(input.readAll()) : QJsonDocument();
        for (const auto& candidate : snapshot.array())
        {
            const auto disk = candidate.toObject();
            const auto path = disk.value("path").toString();
            const auto model = disk.value("model").toString().simplified();
            const auto size = disk.value("size").toDouble() / (1024.0 * 1024 * 1024);
            auto description = tr("%1 · %2 GiB").arg(path, QString::number(size, 'f', 1));
            if (!model.isEmpty())
                description += QStringLiteral(" · ") + model;
            auto* item = new QListWidgetItem(description, m_disks);
            item->setData(Qt::UserRole, disk);
        }
        updateSelection();
        if (!snapshot.isArray())
            m_hint->setText(tr("Could not read the disk list. Check again."));
    }

    static QLabel* label(const QString& text)
    {
        auto* result = new QLabel(text);
        result->setTextFormat(Qt::PlainText);
        result->setWordWrap(true);
        return result;
    }

    QJsonObject selectedDisk() const
    {
        const auto selection = m_disks ? m_disks->selectedItems() : QList<QListWidgetItem*>();
        return selection.isEmpty() ? QJsonObject {} : selection.constFirst()->data(Qt::UserRole).toJsonObject();
    }

    void updateSelection()
    {
        const auto disk = selectedDisk();
        const auto path = disk.value("path").toString();
        const auto serial = disk.value("serial").toString().simplified();
        const auto wwn = disk.value("wwn").toString().simplified();
        const auto deviceId = disk.value("maj:min").toString();
        QStringList details;
        if (!path.isEmpty())
        {
            if (!serial.isEmpty())
                details << tr("Serial: %1").arg(serial);
            if (!wwn.isEmpty())
                details << tr("WWN: %1").arg(wwn);
            details << tr("Device ID: %1").arg(deviceId);
        }
        m_details->setText(details.join(QStringLiteral("  ·  ")));
        m_details->setVisible(!path.isEmpty());
        const bool ready = isNextEnabled();
        if (!m_disks->count())
            m_hint->setText(tr("No eligible disks found. Connect an empty, fixed disk of at least 32 GiB and check again."));
        else if (!ready)
            m_hint->setText(tr("Select the disk you want to use."));
        else
            m_hint->setText(tr("Review this choice before selecting Install ConstOS."));

        auto* state = Calamares::JobQueue::instance()->globalStorage();
        const auto selection = ready ? QString::fromUtf8(QJsonDocument(disk).toJson(QJsonDocument::Compact)) : QString();
        state->insert(QStringLiteral("constosDiskSelection"), selection);
        Q_EMIT nextStatusChanged(ready);
    }

    QWidget* m_page = nullptr;
    QListWidget* m_disks = nullptr;
    QLabel* m_details = nullptr;
    QLabel* m_hint = nullptr;
    QPushButton* m_refresh = nullptr;
};

CALAMARES_PLUGIN_FACTORY_DECLARATION(DiskStepFactory)
CALAMARES_PLUGIN_FACTORY_DEFINITION(DiskStepFactory, registerPlugin<DiskStep>();)

#include "constosdisk.moc"
