USE [Khan]
GO

/****** Object:  Table [dbo].[badge_detail]    Script Date: 02/07/2014 18:25:20 ******/
IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[badge_detail]') AND type in (N'U'))
DROP TABLE [dbo].[badge_detail]
GO

USE [Khan]
GO

/****** Object:  Table [dbo].[badge_detail]    Script Date: 02/07/2014 18:25:21 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

SET ANSI_PADDING ON
GO

CREATE TABLE [dbo].[badge_detail](
	[context] [varchar](255) NULL,
	[slug] [varchar](255) NULL,
	[student] [varchar](255) NULL,
	[date_earned] [datetime] NULL
) ON [PRIMARY]

GO

SET ANSI_PADDING OFF
GO


